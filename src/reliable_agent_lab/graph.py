from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Annotated, Any, TypedDict
from uuid import UUID

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import ValidationError

from reliable_agent_lab.evidence import InvestigationCapabilities
from reliable_agent_lab.mcp_contracts import CapabilityError, ToolErrorCode
from reliable_agent_lab.models import (
    ActionExecution,
    ApprovalRequest,
    RemediationPlan,
    ReportStatus,
    SpecialistReport,
    SpecialistRole,
)
from reliable_agent_lab.operations import ActionLedger, ResetOperation
from reliable_agent_lab.remediation import (
    RecoveryCapability,
    RemediationAgent,
    RiskPolicy,
    VerifierAgent,
)
from reliable_agent_lab.specialists import (
    InvestigationTask,
    LogsAgent,
    MetricsAgent,
    TraceAgent,
    failed_report,
)
from reliable_agent_lab.telemetry import get_tracer

GraphEventSink = Callable[[str, str, dict[str, object]], Awaitable[None]]


def merge_reports(
    current: list[dict[str, Any]], updates: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Replace on role identity, so retries and checkpoint replay do not duplicate reports."""
    merged = {report["role"]: report for report in current}
    merged.update({report["role"]: report for report in updates})
    return [merged[role] for role in sorted(merged)]


class IncidentGraphState(TypedDict, total=False):
    incident_id: str
    run_id: str
    service: str
    symptom: str
    reports: Annotated[list[dict[str, Any]], merge_reports]
    diagnosis: str
    error_code: str | None
    remediation_plan: dict[str, Any] | None
    approval: str | None
    execution: dict[str, Any] | None
    verification: dict[str, Any] | None


def build_incident_graph(
    capabilities: InvestigationCapabilities,
    event_sink: GraphEventSink | None = None,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
    operations: ResetOperation | None = None,
    recovery: RecoveryCapability | None = None,
    action_ledger: ActionLedger | None = None,
) -> Any:
    if (operations is None) != (recovery is None):
        raise ValueError("operations and recovery must be configured together")
    if operations is not None and checkpointer is None:
        raise ValueError("approval workflow requires a checkpointer")
    metrics = MetricsAgent(capabilities.metrics)
    logs = LogsAgent(capabilities.logs)
    trace_agent = TraceAgent(capabilities.traces)
    remediation = RemediationAgent()
    policy = RiskPolicy()
    verifier = VerifierAgent(recovery) if recovery is not None else None
    tracer = get_tracer("reliable_agent_lab.graph")

    def traced(name: str, node: Any) -> Any:
        async def run(state: IncidentGraphState) -> Any:
            with tracer.start_as_current_span(name) as span:
                span.set_attribute("ral.incident_id", state["incident_id"])
                span.set_attribute("ral.run_id", state.get("run_id", ""))
                return await node(state)

        return run

    async def emit(incident_id: str, event_type: str, data: dict[str, object]) -> None:
        if event_sink is not None:
            await event_sink(incident_id, event_type, data)

    async def supervisor_delegate(state: IncidentGraphState) -> dict[str, object]:
        await emit(
            state["incident_id"],
            "delegation.planned",
            {"agents": [role.value for role in SpecialistRole]},
        )
        return {}

    def specialist_node(agent: MetricsAgent | LogsAgent | TraceAgent) -> Any:
        async def run(state: IncidentGraphState) -> dict[str, list[dict[str, Any]]]:
            incident_id = state["incident_id"]
            await emit(incident_id, "delegation.started", {"agent": agent.role.value})
            tool_name = {
                SpecialistRole.METRICS: "query_service_metrics",
                SpecialistRole.LOGS: "query_recent_logs",
                SpecialistRole.TRACE: "query_service_traces",
            }[agent.role]
            await emit(
                incident_id,
                "tool.started",
                {"agent": agent.role.value, "tool": tool_name},
            )
            task = InvestigationTask(
                incident_id=incident_id,
                service=state["service"],
                symptom=state["symptom"],
            )
            try:
                with tracer.start_as_current_span(f"tool.{tool_name}") as span:
                    span.set_attribute("ral.incident_id", incident_id)
                    span.set_attribute("ral.agent_role", agent.role.value)
                    span.set_attribute("ral.tool_name", tool_name)
                    report = await agent.investigate(task)
            except CapabilityError as exc:
                report = failed_report(agent.role, exc.code.value)
            except TimeoutError:
                report = failed_report(agent.role, "TOOL_TIMEOUT")
            except Exception:
                report = failed_report(agent.role, "TOOL_FAILURE")
            await emit(
                incident_id,
                "tool.failed" if report.status == ReportStatus.FAILED else "tool.completed",
                {
                    "agent": agent.role.value,
                    "tool": tool_name,
                    "error_code": report.error_code,
                },
            )
            await emit(
                incident_id,
                "delegation.completed",
                {
                    "agent": agent.role.value,
                    "status": report.status.value,
                    "evidence_refs": report.evidence_refs,
                    "error_code": report.error_code,
                },
            )
            return {"reports": [report.model_dump(mode="json")]}

        return run

    async def supervisor_fuse(state: IncidentGraphState) -> dict[str, str | None]:
        reports = {
            report.role: report
            for report in (SpecialistReport.model_validate(item) for item in state["reports"])
        }
        metric_report = reports.get(SpecialistRole.METRICS)
        log_report = reports.get(SpecialistRole.LOGS)
        trace_report = reports.get(SpecialistRole.TRACE)
        if (
            metric_report is None
            or log_report is None
            or metric_report.status != ReportStatus.COMPLETE
            or log_report.status != ReportStatus.COMPLETE
        ):
            diagnosis = "insufficient metrics or log evidence for root-cause diagnosis"
            error_code = "INSUFFICIENT_EVIDENCE"
        else:
            redis_fault = any(
                item.payload.get("redisUnavailable") is True for item in metric_report.evidence
            )
            mysql_fault = any(
                item.payload.get("mysqlUnavailable") is True for item in metric_report.evidence
            )
            inventory_fault = any(
                item.payload.get("inventoryLatencyActive") is True
                for item in metric_report.evidence
            )
            payment_fault = any(
                item.payload.get("paymentHttp5xxActive") is True for item in metric_report.evidence
            )
            redis_log_confirms = "Redis cache dependency unavailable" in log_report.hypotheses
            mysql_log_confirms = "MySQL dependency unavailable" in log_report.hypotheses

            def fault_start_ns(field: str) -> int | None:
                for item in metric_report.evidence:
                    value = item.payload.get(field)
                    if isinstance(value, str) and value:
                        try:
                            return int(datetime.fromisoformat(value).timestamp() * 1_000_000_000)
                        except ValueError:
                            return None
                return None

            def fresh_log(event_type: str, since_ns: int | None) -> bool:
                if since_ns is None:
                    return False
                for evidence in log_report.evidence:
                    events = evidence.payload.get("events", [])
                    if not isinstance(events, list):
                        continue
                    for event in events:
                        if not isinstance(event, dict) or event.get("type") != event_type:
                            continue
                        observed = event.get("observedAt")
                        if isinstance(observed, str):
                            try:
                                if (
                                    datetime.fromisoformat(observed).timestamp() * 1_000_000_000
                                    >= since_ns
                                ):
                                    return True
                            except ValueError:
                                pass
                return False

            def fresh_trace(service: str, name: str, since_ns: int | None, *, slow: bool) -> bool:
                if (
                    since_ns is None
                    or trace_report is None
                    or trace_report.status != ReportStatus.COMPLETE
                ):
                    return False
                for evidence in trace_report.evidence:
                    spans = evidence.payload.get("spans", [])
                    if not isinstance(spans, list):
                        continue
                    for span in spans:
                        if (
                            not isinstance(span, dict)
                            or span.get("service") != service
                            or span.get("name") != name
                        ):
                            continue
                        try:
                            recent = int(span.get("start_time_unix_nano", "0")) >= since_ns
                            corroborates = int(
                                span.get("duration_ms" if slow else "http_status", "0")
                            ) >= (500 if slow else 500)
                        except (TypeError, ValueError):
                            continue
                        if recent and corroborates:
                            return True
                return False

            inventory_started = fault_start_ns("inventoryFaultStartedAt")
            payment_started = fault_start_ns("paymentFaultStartedAt")
            inventory_confirmed = (
                "Inventory downstream latency" in log_report.hypotheses
                and trace_report is not None
                and "Inventory downstream latency" in trace_report.hypotheses
                and fresh_log("order_inventory_slow", inventory_started)
                and fresh_trace(
                    "inventory-service", "GET /api/inventory/{sku}", inventory_started, slow=True
                )
            )
            payment_confirmed = (
                "Payment downstream HTTP 5xx" in log_report.hypotheses
                and trace_report is not None
                and "Payment downstream HTTP 5xx" in trace_report.hypotheses
                and fresh_log("order_payment_request_failed", payment_started)
                and fresh_trace(
                    "payment-service",
                    "GET /api/payments/authorization-preview",
                    payment_started,
                    slow=False,
                )
            )

            if sum((redis_fault, mysql_fault, inventory_fault, payment_fault)) > 1:
                diagnosis = "multiple controlled faults are active; root cause is ambiguous"
                error_code = "INSUFFICIENT_EVIDENCE"
            elif redis_fault and redis_log_confirms:
                diagnosis = "controlled Redis unavailability detected; MySQL remains authoritative"
                error_code = None
            elif mysql_fault and mysql_log_confirms:
                diagnosis = "controlled MySQL unavailability detected; uncached order reads fail"
                error_code = None
            elif inventory_fault and inventory_confirmed:
                diagnosis = "controlled inventory downstream latency detected in checkout preview"
                error_code = None
            elif payment_fault and payment_confirmed:
                diagnosis = "controlled payment downstream HTTP 5xx detected in checkout preview"
                error_code = None
            elif redis_fault:
                diagnosis = (
                    "Redis fault state is active, but logs do not confirm a cache read failure"
                )
                error_code = "INSUFFICIENT_EVIDENCE"
            elif mysql_fault:
                diagnosis = "MySQL fault state is active, but logs do not confirm a failed read"
                error_code = "INSUFFICIENT_EVIDENCE"
            elif inventory_fault or payment_fault:
                diagnosis = (
                    "downstream fault is active, but fresh logs and trace do not jointly confirm it"
                )
                error_code = "INSUFFICIENT_EVIDENCE"
            else:
                diagnosis = "no controlled Redis fault detected"
                error_code = None
        await emit(
            state["incident_id"],
            "diagnosis.updated",
            {
                "diagnosis": diagnosis,
                "error_code": error_code,
                "report_roles": sorted(role.value for role in reports),
            },
        )
        return {"diagnosis": diagnosis, "error_code": error_code}

    async def remediation_node(state: IncidentGraphState) -> dict[str, object]:
        plan = remediation.propose(
            UUID(state["incident_id"]), state["diagnosis"], state.get("error_code")
        )
        if plan is None:
            return {"remediation_plan": None}
        await emit(
            state["incident_id"],
            "remediation.proposed",
            {"action_id": str(plan.action_id), "action": plan.action, "risk": plan.risk},
        )
        return {"remediation_plan": plan.model_dump(mode="json")}

    async def policy_node(state: IncidentGraphState) -> dict[str, object]:
        plan = RemediationPlan.model_validate(state["remediation_plan"])
        required = policy.approval_required(plan)
        await emit(
            state["incident_id"],
            "policy.evaluated",
            {"action_id": str(plan.action_id), "approval_required": required},
        )
        if not required:
            raise ValueError("all v0.1 mutation plans must require approval")
        return {}

    async def approval_node(state: IncidentGraphState) -> dict[str, object]:
        plan = RemediationPlan.model_validate(state["remediation_plan"])
        decision = interrupt(
            {
                "action_id": str(plan.action_id),
                "action": plan.action,
                "target": plan.target,
                "risk": plan.risk,
            }
        )
        try:
            approved = ApprovalRequest.model_validate(decision)
        except ValidationError as exc:
            raise ValueError("invalid approval payload") from exc
        if approved.action_id != plan.action_id:
            raise ValueError("approval action id does not match the plan")
        await emit(
            state["incident_id"],
            "approval.decided",
            {"action_id": str(plan.action_id), "approved": approved.approved},
        )
        return {
            "approval": "approved" if approved.approved else "rejected",
            "error_code": None if approved.approved else "APPROVAL_REJECTED",
        }

    async def execute_node(state: IncidentGraphState) -> dict[str, object]:
        assert operations is not None
        plan = RemediationPlan.model_validate(state["remediation_plan"])
        if action_ledger is not None:
            previous = await action_ledger.begin_action(UUID(state["incident_id"]), plan.action_id)
            if previous is not None:
                replayed = previous.model_copy(update={"duplicate": True})
                await emit(
                    state["incident_id"],
                    "remediation.replayed",
                    {"action_id": str(plan.action_id), "status": replayed.status},
                )
                return {
                    "execution": replayed.model_dump(mode="json"),
                    "error_code": replayed.error_code,
                }
        for attempt in (1, 2):
            await emit(
                state["incident_id"],
                "tool.started",
                {"agent": "remediation", "tool": plan.action, "attempt": attempt},
            )
            try:
                with tracer.start_as_current_span(f"tool.{plan.action}") as span:
                    span.set_attribute("ral.incident_id", state["incident_id"])
                    span.set_attribute("ral.agent_role", "remediation")
                    span.set_attribute("ral.action_id", str(plan.action_id))
                    span.set_attribute("ral.retry_attempt", attempt)
                    if plan.action == "reset_redis_fault":
                        result = await operations.reset_redis_fault(plan.action_id)
                    elif plan.action == "reset_mysql_fault":
                        result = await operations.reset_mysql_fault(plan.action_id)
                    elif plan.action == "reset_inventory_latency":
                        result = await operations.reset_inventory_latency(plan.action_id)
                    else:
                        result = await operations.reset_payment_5xx(plan.action_id)
                if (
                    result.redis_unavailable
                    or result.mysql_unavailable
                    or result.inventory_latency
                    or result.payment_http5xx
                ):
                    raise CapabilityError(ToolErrorCode.OPERATION, "fault remained active")
                execution = ActionExecution(
                    action_id=plan.action_id,
                    status="completed",
                    duplicate=result.duplicate,
                )
                if action_ledger is not None:
                    await action_ledger.finish_action(execution)
                await emit(
                    state["incident_id"],
                    "tool.completed",
                    {"agent": "remediation", "tool": plan.action, "attempt": attempt},
                )
                return {"execution": execution.model_dump(mode="json"), "error_code": None}
            except CapabilityError as exc:
                code = exc.code.value
                await emit(
                    state["incident_id"],
                    "tool.failed",
                    {
                        "agent": "remediation",
                        "tool": plan.action,
                        "attempt": attempt,
                        "error_code": code,
                    },
                )
                if attempt == 1 and exc.code in {ToolErrorCode.TIMEOUT, ToolErrorCode.DEPENDENCY}:
                    continue
                execution = ActionExecution(
                    action_id=plan.action_id,
                    status="failed",
                    error_code=code,
                )
                if action_ledger is not None:
                    await action_ledger.finish_action(execution)
                return {"execution": execution.model_dump(mode="json"), "error_code": code}
        raise AssertionError("bounded operation loop exhausted")

    async def verifier_node(state: IncidentGraphState) -> dict[str, object]:
        assert verifier is not None
        plan = RemediationPlan.model_validate(state["remediation_plan"])
        tool_name = {
            "reset_redis_fault": "probe_cache_recovery",
            "reset_mysql_fault": "probe_mysql_recovery",
            "reset_inventory_latency": "probe_inventory_recovery",
            "reset_payment_5xx": "probe_payment_recovery",
        }[plan.action]
        await emit(
            state["incident_id"],
            "tool.started",
            {"agent": "verifier", "tool": tool_name},
        )
        try:
            with tracer.start_as_current_span(f"tool.{tool_name}") as span:
                span.set_attribute("ral.incident_id", state["incident_id"])
                span.set_attribute("ral.agent_role", "verifier")
                verification = await verifier.verify(state["service"], plan.action)
        except CapabilityError as exc:
            await emit(
                state["incident_id"],
                "tool.failed",
                {"agent": "verifier", "tool": tool_name, "error_code": exc.code.value},
            )
            return {"verification": None, "error_code": exc.code.value}
        await emit(
            state["incident_id"],
            "verification.completed",
            verification.model_dump(mode="json"),
        )
        return {
            "verification": verification.model_dump(mode="json"),
            "error_code": None if verification.status == "resolved" else "VERIFICATION_FAILED",
        }

    graph = StateGraph(IncidentGraphState)
    graph.add_node("supervisor_delegate", traced("agent.supervisor.delegate", supervisor_delegate))
    graph.add_node("metrics_agent", traced("agent.metrics", specialist_node(metrics)))
    graph.add_node("logs_agent", traced("agent.logs", specialist_node(logs)))
    graph.add_node("trace_agent", traced("agent.trace", specialist_node(trace_agent)))
    graph.add_node("supervisor_fuse", traced("agent.supervisor.fuse", supervisor_fuse))
    graph.add_edge(START, "supervisor_delegate")
    for node in ("metrics_agent", "logs_agent", "trace_agent"):
        graph.add_edge("supervisor_delegate", node)
    graph.add_edge(["metrics_agent", "logs_agent", "trace_agent"], "supervisor_fuse")
    if operations is None:
        graph.add_edge("supervisor_fuse", END)
    else:
        graph.add_node("remediation_agent", traced("agent.remediation", remediation_node))
        graph.add_node("risk_policy", traced("policy.risk", policy_node))
        graph.add_node("approval_gate", traced("approval.gate", approval_node))
        graph.add_node("execute_operation", traced("operation.execute", execute_node))
        graph.add_node("verifier_agent", traced("agent.verifier", verifier_node))
        graph.add_edge("supervisor_fuse", "remediation_agent")
        graph.add_conditional_edges(
            "remediation_agent",
            lambda state: "risk_policy" if state.get("remediation_plan") else END,
        )
        graph.add_edge("risk_policy", "approval_gate")
        graph.add_conditional_edges(
            "approval_gate",
            lambda state: "execute_operation" if state.get("approval") == "approved" else END,
        )
        graph.add_conditional_edges(
            "execute_operation",
            lambda state: "verifier_agent" if state.get("error_code") is None else END,
        )
        graph.add_edge("verifier_agent", END)
    return graph.compile(checkpointer=checkpointer)
