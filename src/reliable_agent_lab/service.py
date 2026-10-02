import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from reliable_agent_lab.evidence import InvestigationCapabilities
from reliable_agent_lab.graph import build_incident_graph
from reliable_agent_lab.models import (
    ActionExecution,
    ApprovalDecision,
    ApprovalRequest,
    Evidence,
    IncidentCreateRequest,
    IncidentEvent,
    IncidentResponse,
    IncidentStatus,
    RemediationPlan,
    SpecialistReport,
    VerificationResult,
)
from reliable_agent_lab.operations import ResetOperation
from reliable_agent_lab.remediation import RecoveryCapability
from reliable_agent_lab.store import IncidentStore, InMemoryIncidentStore
from reliable_agent_lab.telemetry import get_tracer


class IncidentNotFoundError(KeyError):
    pass


class ApprovalConflictError(ValueError):
    pass


class IncidentService:
    def __init__(
        self,
        capabilities: InvestigationCapabilities,
        store: IncidentStore | None = None,
        checkpointer: BaseCheckpointSaver[Any] | None = None,
        operations: ResetOperation | None = None,
        recovery: RecoveryCapability | None = None,
    ) -> None:
        self._store = store or InMemoryIncidentStore()
        self._graph = build_incident_graph(
            capabilities,
            self._graph_event,
            checkpointer,
            operations,
            recovery,
            self._store if operations is not None else None,
        )
        self._conditions: dict[UUID, asyncio.Condition] = {}
        self._approval_locks: dict[UUID, asyncio.Lock] = {}
        self._tasks: dict[UUID, asyncio.Task[None]] = {}

    async def setup(self) -> None:
        await self._store.setup()
        for incident in await self._store.incomplete():
            snapshot = await self._graph.aget_state(
                {"configurable": {"thread_id": str(incident.run_id)}}
            )
            if snapshot.values and not snapshot.next:
                await self._handle_result(incident.id, dict(snapshot.values))
                continue
            if incident.approval in {ApprovalDecision.APPROVED, ApprovalDecision.REJECTED}:
                assert incident.remediation_plan is not None
                self._launch(
                    incident.id,
                    ApprovalRequest(
                        action_id=incident.remediation_plan.action_id,
                        approved=incident.approval == ApprovalDecision.APPROVED,
                    ),
                )
            else:
                self._launch(
                    incident.id,
                    continue_existing=bool(snapshot.values),
                )

    def _condition(self, incident_id: UUID) -> asyncio.Condition:
        return self._conditions.setdefault(incident_id, asyncio.Condition())

    def _launch(
        self,
        incident_id: UUID,
        approval: ApprovalRequest | None = None,
        *,
        continue_existing: bool = False,
    ) -> None:
        if incident_id in self._tasks and not self._tasks[incident_id].done():
            return
        task = asyncio.create_task(self._run(incident_id, approval, continue_existing))
        self._tasks[incident_id] = task
        task.add_done_callback(lambda _: self._tasks.pop(incident_id, None))

    async def create(self, request: IncidentCreateRequest) -> IncidentResponse:
        now = datetime.now(UTC)
        incident = IncidentResponse(
            id=uuid4(),
            run_id=uuid4(),
            service=request.service,
            symptom=request.symptom,
            severity=request.severity,
            scenario_id=request.scenario_id,
            status=IncidentStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        await self._store.create(incident)
        await self._publish(incident.id, "incident.created", {"status": incident.status})
        self._launch(incident.id)
        return incident.model_copy(deep=True)

    async def approve(self, incident_id: UUID, request: ApprovalRequest) -> IncidentResponse:
        lock = self._approval_locks.setdefault(incident_id, asyncio.Lock())
        async with lock:
            incident = await self.get(incident_id)
            plan = incident.remediation_plan
            if plan is None or plan.action_id != request.action_id:
                raise ApprovalConflictError("action does not match a pending plan")
            decision = ApprovalDecision.APPROVED if request.approved else ApprovalDecision.REJECTED
            if incident.approval == decision:
                return incident
            if (
                incident.status != IncidentStatus.AWAITING_APPROVAL
                or incident.approval != ApprovalDecision.PENDING
            ):
                raise ApprovalConflictError("approval is not pending or decision conflicts")
            incident.approval = decision
            incident.status = IncidentStatus.RUNNING
            incident.updated_at = datetime.now(UTC)
            await self._store.save(incident)
            await self._publish(
                incident_id,
                "approval.submitted",
                {"action_id": str(request.action_id), "approved": request.approved},
            )
            self._launch(incident_id, request)
            return incident

    async def get(self, incident_id: UUID) -> IncidentResponse:
        incident = await self._store.get(incident_id)
        if incident is None:
            raise IncidentNotFoundError(str(incident_id))
        return incident

    async def events(self, incident_id: UUID) -> AsyncIterator[IncidentEvent]:
        await self.get(incident_id)
        index = 0
        condition = self._condition(incident_id)
        while True:
            history = await self._store.events_after(incident_id, index)
            for event in history:
                index = event.sequence
                yield event
                if event.type in {"incident.completed", "incident.failed"}:
                    return
                if event.type == "approval.required":
                    incident = await self.get(incident_id)
                    if incident.status == IncidentStatus.AWAITING_APPROVAL:
                        return
            async with condition:
                try:
                    await asyncio.wait_for(condition.wait(), timeout=0.5)
                except TimeoutError:
                    pass

    async def _run(
        self,
        incident_id: UUID,
        approval: ApprovalRequest | None = None,
        continue_existing: bool = False,
    ) -> None:
        incident = await self.get(incident_id)
        incident.status = IncidentStatus.RUNNING
        incident.updated_at = datetime.now(UTC)
        await self._store.save(incident)
        try:
            graph_input: Any
            if approval is not None:
                graph_input = Command(resume=approval.model_dump(mode="json"))
            elif continue_existing:
                graph_input = None
            else:
                graph_input = {
                    "incident_id": str(incident.id),
                    "run_id": str(incident.run_id),
                    "service": incident.service,
                    "symptom": incident.symptom,
                }
            span_name = "incident.resume" if approval is not None else "incident.run"
            with get_tracer("reliable_agent_lab.service").start_as_current_span(span_name) as span:
                span.set_attribute("ral.incident_id", str(incident.id))
                span.set_attribute("ral.run_id", str(incident.run_id))
                span.set_attribute("ral.scenario_id", incident.scenario_id or "")
                result = await self._graph.ainvoke(
                    graph_input,
                    config={
                        "recursion_limit": 16,
                        "configurable": {"thread_id": str(incident.run_id)},
                    },
                )
            await self._handle_result(incident_id, result)
        except Exception:
            incident.status = IncidentStatus.FAILED
            incident.error_code = "WORKFLOW_FAILED"
            incident.updated_at = datetime.now(UTC)
            await self._store.save(incident)
            await self._publish(
                incident_id,
                "incident.failed",
                {"error_code": incident.error_code},
            )

    async def _handle_result(self, incident_id: UUID, result: dict[str, Any]) -> None:
        incident = await self.get(incident_id)
        incident.specialist_reports = [
            SpecialistReport.model_validate(item) for item in result["reports"]
        ]
        incident.evidence = [
            Evidence.model_validate(evidence)
            for report in incident.specialist_reports
            for evidence in report.evidence
        ]
        incident.diagnosis = str(result["diagnosis"])
        incident.error_code = result.get("error_code")
        if result.get("remediation_plan") is not None:
            incident.remediation_plan = RemediationPlan.model_validate(result["remediation_plan"])
        if result.get("execution") is not None:
            incident.execution = ActionExecution.model_validate(result["execution"])
        if result.get("verification") is not None:
            incident.verification = VerificationResult.model_validate(result["verification"])
        if "__interrupt__" in result:
            incident.status = IncidentStatus.AWAITING_APPROVAL
            incident.approval = ApprovalDecision.PENDING
            incident.updated_at = datetime.now(UTC)
            await self._store.save(incident)
            assert incident.remediation_plan is not None
            await self._publish(
                incident_id,
                "approval.required",
                {"action_id": str(incident.remediation_plan.action_id)},
            )
            return
        incident.status = IncidentStatus.FAILED if incident.error_code else IncidentStatus.COMPLETED
        incident.updated_at = datetime.now(UTC)
        await self._store.save(incident)
        await self._publish(
            incident_id,
            "incident.failed" if incident.error_code else "incident.completed",
            {"status": incident.status, "error_code": incident.error_code},
        )

    async def _graph_event(
        self, incident_id: str, event_type: str, data: dict[str, object]
    ) -> None:
        await self._publish(UUID(incident_id), event_type, data)

    async def _publish(self, incident_id: UUID, event_type: str, data: dict[str, object]) -> None:
        incident = await self.get(incident_id)
        await self._store.append_event(
            IncidentEvent(
                sequence=0,
                incident_id=incident_id,
                run_id=incident.run_id,
                type=event_type,
                data=data,
            )
        )
        condition = self._condition(incident_id)
        async with condition:
            condition.notify_all()
