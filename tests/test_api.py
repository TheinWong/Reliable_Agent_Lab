import asyncio
import time
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver

from reliable_agent_lab.api import create_app
from reliable_agent_lab.evidence import InvestigationCapabilities
from reliable_agent_lab.mcp_contracts import CacheRecoveryProbe, ResetFaultResult
from reliable_agent_lab.models import (
    ApprovalDecision,
    ApprovalRequest,
    IncidentCreateRequest,
    IncidentStatus,
)
from reliable_agent_lab.service import IncidentService
from reliable_agent_lab.store import InMemoryIncidentStore


class FakeMetrics:
    async def query_metrics(self, service: str) -> dict[str, object]:
        return {"redisUnavailable": True}


class FakeLogs:
    async def query_logs(self, service: str) -> dict[str, object]:
        return {
            "events": [
                {"type": "demo_fault_injected", "dependency": "redis"},
                {"type": "order_cache_read_failed", "dependency": "redis"},
            ]
        }


class FakeTraces:
    async def query_traces(self, service: str) -> dict[str, object]:
        return {"available": False, "reason": "not configured"}


def fake_capabilities() -> InvestigationCapabilities:
    return InvestigationCapabilities(FakeMetrics(), FakeLogs(), FakeTraces())


def test_incident_runs_in_background_and_exposes_result() -> None:
    with TestClient(create_app(fake_capabilities())) as client:
        response = client.post(
            "/api/incidents",
            json={"service": "order-service", "symptom": "orders use DB fallback"},
        )
        assert response.status_code == 202
        incident_id = response.json()["id"]
        run_id = response.json()["run_id"]

        for _ in range(50):
            result = client.get(f"/api/incidents/{incident_id}")
            if result.json()["status"] in {"completed", "failed"}:
                break
            time.sleep(0.01)

        assert result.status_code == 200
        assert result.json()["status"] == "completed"
        assert result.json()["run_id"] == run_id
        assert {report["role"] for report in result.json()["specialist_reports"]} == {
            "metrics",
            "logs",
            "trace",
        }
        assert len(result.json()["evidence"]) == 2


def test_missing_incident_has_stable_error_code() -> None:
    with TestClient(create_app(fake_capabilities())) as client:
        response = client.get("/api/incidents/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "INCIDENT_NOT_FOUND"


class FakeOperations:
    def __init__(self) -> None:
        self.calls: list[UUID] = []

    async def reset_redis_fault(self, action_id: UUID) -> ResetFaultResult:
        self.calls.append(action_id)
        return ResetFaultResult(action_id=action_id, scope="local-demo")


class FakeRecovery:
    def __init__(self) -> None:
        self.calls = 0

    async def probe_recovery(self, service: str) -> CacheRecoveryProbe:
        self.calls += 1
        return CacheRecoveryProbe(
            service="order-service",
            fault_cleared=True,
            first_source="DATABASE",
            second_source="CACHE",
        )


def wait_for_status(client: TestClient, incident_id: str, wanted: str) -> dict[str, object]:
    for _ in range(100):
        response = client.get(f"/api/incidents/{incident_id}")
        assert response.status_code == 200
        incident: dict[str, object] = response.json()
        if incident["status"] == wanted:
            return incident
        time.sleep(0.01)
    raise AssertionError(f"incident never reached {wanted}: {incident}")


def test_approval_api_requires_matching_action_and_deduplicates_decision() -> None:
    operations = FakeOperations()
    recovery = FakeRecovery()
    with TestClient(create_app(fake_capabilities(), operations, recovery)) as client:
        created = client.post(
            "/api/incidents", json={"service": "order-service", "symptom": "Redis unavailable"}
        )
        incident_id = created.json()["id"]
        paused = wait_for_status(client, incident_id, "awaiting_approval")
        assert operations.calls == []
        plan = paused["remediation_plan"]
        assert isinstance(plan, dict)
        action_id = plan["action_id"]

        mismatch = client.post(
            f"/api/incidents/{incident_id}/approval",
            json={"action_id": str(uuid4()), "approved": True},
        )
        assert mismatch.status_code == 409
        approval = {"action_id": action_id, "approved": True}
        first = client.post(f"/api/incidents/{incident_id}/approval", json=approval)
        assert first.status_code == 202
        result = wait_for_status(client, incident_id, "completed")
        second = client.post(f"/api/incidents/{incident_id}/approval", json=approval)
        assert second.status_code == 202
        conflict = client.post(
            f"/api/incidents/{incident_id}/approval",
            json={"action_id": action_id, "approved": False},
        )
        assert conflict.status_code == 409
        assert result["verification"]["status"] == "resolved"
        assert operations.calls == [UUID(action_id)]
        assert recovery.calls == 1


def test_denied_approval_never_executes() -> None:
    operations = FakeOperations()
    recovery = FakeRecovery()
    with TestClient(create_app(fake_capabilities(), operations, recovery)) as client:
        created = client.post(
            "/api/incidents", json={"service": "order-service", "symptom": "Redis unavailable"}
        )
        incident_id = created.json()["id"]
        paused = wait_for_status(client, incident_id, "awaiting_approval")
        plan = paused["remediation_plan"]
        assert isinstance(plan, dict)
        denied = client.post(
            f"/api/incidents/{incident_id}/approval",
            json={"action_id": plan["action_id"], "approved": False},
        )
        assert denied.status_code == 202
        result = wait_for_status(client, incident_id, "failed")
        assert result["error_code"] == "APPROVAL_REJECTED"
        assert operations.calls == []
        assert recovery.calls == 0


async def test_restart_recovers_decision_saved_before_resume_task() -> None:
    store = InMemoryIncidentStore()
    checkpointer = InMemorySaver()
    operations = FakeOperations()
    recovery = FakeRecovery()
    first = IncidentService(fake_capabilities(), store, checkpointer, operations, recovery)
    await first.setup()
    created = await first.create(
        IncidentCreateRequest(service="order-service", symptom="Redis unavailable")
    )
    for _ in range(100):
        paused = await first.get(created.id)
        if paused.status == IncidentStatus.AWAITING_APPROVAL:
            break
        await asyncio.sleep(0.01)
    assert paused.status == IncidentStatus.AWAITING_APPROVAL
    assert paused.remediation_plan is not None
    assert operations.calls == []

    # Model a crash after durable approval write but before the background resume task starts.
    paused.approval = ApprovalDecision.APPROVED
    paused.status = IncidentStatus.RUNNING
    await store.save(paused)
    resumed = IncidentService(fake_capabilities(), store, checkpointer, operations, recovery)
    await resumed.setup()
    for _ in range(100):
        completed = await resumed.get(created.id)
        if completed.status == IncidentStatus.COMPLETED:
            break
        await asyncio.sleep(0.01)
    assert completed.status == IncidentStatus.COMPLETED
    assert operations.calls == [paused.remediation_plan.action_id]
    assert recovery.calls == 1


async def test_restart_reconciles_finished_checkpoint_without_replaying_operation() -> None:
    store = InMemoryIncidentStore()
    checkpointer = InMemorySaver()
    operations = FakeOperations()
    recovery = FakeRecovery()
    first = IncidentService(fake_capabilities(), store, checkpointer, operations, recovery)
    await first.setup()
    created = await first.create(
        IncidentCreateRequest(service="order-service", symptom="Redis unavailable")
    )
    for _ in range(100):
        paused = await first.get(created.id)
        if paused.status == IncidentStatus.AWAITING_APPROVAL:
            break
        await asyncio.sleep(0.01)
    assert paused.remediation_plan is not None
    await first.approve(
        created.id,
        ApprovalRequest(action_id=paused.remediation_plan.action_id, approved=True),
    )
    for _ in range(100):
        completed = await first.get(created.id)
        if completed.status == IncidentStatus.COMPLETED:
            break
        await asyncio.sleep(0.01)
    assert completed.status == IncidentStatus.COMPLETED
    assert len(operations.calls) == 1

    # Model a crash after graph completion but before its final API projection persisted.
    completed.status = IncidentStatus.RUNNING
    completed.execution = None
    completed.verification = None
    await store.save(completed)
    resumed = IncidentService(fake_capabilities(), store, checkpointer, operations, recovery)
    await resumed.setup()
    recovered = await resumed.get(created.id)
    assert recovered.status == IncidentStatus.COMPLETED
    assert recovered.execution is not None
    assert recovered.verification is not None
    assert len(operations.calls) == 1
