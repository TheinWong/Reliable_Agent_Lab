from uuid import UUID, uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pytest import MonkeyPatch

from reliable_agent_lab.evidence import InvestigationCapabilities
from reliable_agent_lab.graph import build_incident_graph
from reliable_agent_lab.mcp_contracts import (
    CacheRecoveryProbe,
    CapabilityError,
    ResetFaultResult,
    ToolErrorCode,
)
from reliable_agent_lab.store import InMemoryIncidentStore


class Metrics:
    async def query_metrics(self, service: str) -> dict[str, object]:
        return {"redisUnavailable": True, "cacheReadErrors": 1}


class Logs:
    async def query_logs(self, service: str) -> dict[str, object]:
        return {
            "events": [
                {"type": "demo_fault_injected", "dependency": "redis"},
                {"type": "order_cache_read_failed", "dependency": "redis"},
            ]
        }


class Traces:
    async def query_traces(self, service: str) -> dict[str, object]:
        return {"available": False, "reason": "not configured"}


class Operations:
    def __init__(self) -> None:
        self.calls: list[UUID] = []

    async def reset_redis_fault(self, action_id: UUID) -> ResetFaultResult:
        self.calls.append(action_id)
        return ResetFaultResult(action_id=action_id, scope="local-demo")


class Recovery:
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

    async def probe_mysql_recovery(self, service: str) -> CacheRecoveryProbe:
        self.calls += 1
        return CacheRecoveryProbe(
            service="order-service",
            fault_cleared=True,
            first_source="DATABASE",
            second_source="CACHE",
        )


async def test_mysql_recovery_uses_distinct_operation_and_fresh_probe() -> None:
    class MysqlMetrics:
        async def query_metrics(self, service: str) -> dict[str, object]:
            return {"redisUnavailable": False, "mysqlUnavailable": True}

    class MysqlLogs:
        async def query_logs(self, service: str) -> dict[str, object]:
            return {
                "events": [
                    {"type": "demo_fault_injected", "dependency": "mysql"},
                    {"type": "order_mysql_read_failed", "dependency": "mysql"},
                ]
            }

    class MysqlOperations(Operations):
        async def reset_mysql_fault(self, action_id: UUID) -> ResetFaultResult:
            self.calls.append(action_id)
            return ResetFaultResult(action_id=action_id, scope="local-demo")

    operations = MysqlOperations()
    recovery = Recovery()
    graph = build_incident_graph(
        InvestigationCapabilities(MysqlMetrics(), MysqlLogs(), Traces()),
        checkpointer=InMemorySaver(),
        operations=operations,
        recovery=recovery,
    )
    config = {"configurable": {"thread_id": str(uuid4())}}
    paused = await graph.ainvoke(
        {"incident_id": str(uuid4()), "service": "order-service", "symptom": "uncached order 503"},
        config=config,
    )
    assert paused["remediation_plan"]["action"] == "reset_mysql_fault"
    assert operations.calls == []
    resumed = await graph.ainvoke(
        Command(resume={"action_id": paused["remediation_plan"]["action_id"], "approved": True}),
        config=config,
    )
    assert len(operations.calls) == 1
    assert recovery.calls == 1
    assert resumed["verification"]["status"] == "resolved"


async def test_approval_interrupt_precedes_operation_and_verifier_is_fresh() -> None:
    operations = Operations()
    recovery = Recovery()
    graph = build_incident_graph(
        InvestigationCapabilities(Metrics(), Logs(), Traces()),
        checkpointer=InMemorySaver(),
        operations=operations,
        recovery=recovery,
    )
    incident_id = uuid4()
    config = {"configurable": {"thread_id": str(uuid4())}}
    paused = await graph.ainvoke(
        {"incident_id": str(incident_id), "service": "order-service", "symptom": "cache failed"},
        config=config,
    )
    assert "__interrupt__" in paused
    assert operations.calls == []
    assert recovery.calls == 0
    plan = paused["remediation_plan"]
    assert plan["action"] == "reset_redis_fault"

    result = await graph.ainvoke(
        Command(resume={"action_id": plan["action_id"], "approved": True}),
        config=config,
    )
    assert operations.calls == [UUID(plan["action_id"])]
    assert recovery.calls == 1
    assert result["approval"] == "approved"
    assert result["execution"]["status"] == "completed"
    assert result["verification"]["status"] == "resolved"
    assert result["error_code"] is None


async def test_denial_never_calls_operation() -> None:
    operations = Operations()
    recovery = Recovery()
    graph = build_incident_graph(
        InvestigationCapabilities(Metrics(), Logs(), Traces()),
        checkpointer=InMemorySaver(),
        operations=operations,
        recovery=recovery,
    )
    config = {"configurable": {"thread_id": str(uuid4())}}
    paused = await graph.ainvoke(
        {"incident_id": str(uuid4()), "service": "order-service", "symptom": "cache failed"},
        config=config,
    )
    denied = await graph.ainvoke(
        Command(resume={"action_id": paused["remediation_plan"]["action_id"], "approved": False}),
        config=config,
    )
    assert denied["error_code"] == "APPROVAL_REJECTED"
    assert operations.calls == []
    assert recovery.calls == 0


async def test_transient_operation_retry_reuses_action_id() -> None:
    class FlakyOperations(Operations):
        async def reset_redis_fault(self, action_id: UUID) -> ResetFaultResult:
            self.calls.append(action_id)
            if len(self.calls) == 1:
                raise CapabilityError(ToolErrorCode.TIMEOUT, "ambiguous timeout")
            return ResetFaultResult(action_id=action_id, scope="local-demo", duplicate=True)

    operations = FlakyOperations()
    graph = build_incident_graph(
        InvestigationCapabilities(Metrics(), Logs(), Traces()),
        checkpointer=InMemorySaver(),
        operations=operations,
        recovery=Recovery(),
    )
    config = {"configurable": {"thread_id": str(uuid4())}}
    paused = await graph.ainvoke(
        {"incident_id": str(uuid4()), "service": "order-service", "symptom": "cache failed"},
        config=config,
    )
    result = await graph.ainvoke(
        Command(resume={"action_id": paused["remediation_plan"]["action_id"], "approved": True}),
        config=config,
    )
    assert operations.calls == [operations.calls[0], operations.calls[0]]
    assert result["execution"]["duplicate"] is True
    assert result["verification"]["status"] == "resolved"


async def test_verifier_can_report_unresolved_after_successful_operation() -> None:
    class UnresolvedRecovery(Recovery):
        async def probe_recovery(self, service: str) -> CacheRecoveryProbe:
            return CacheRecoveryProbe(
                service="order-service",
                fault_cleared=True,
                first_source="DATABASE",
                second_source="DATABASE",
            )

    graph = build_incident_graph(
        InvestigationCapabilities(Metrics(), Logs(), Traces()),
        checkpointer=InMemorySaver(),
        operations=Operations(),
        recovery=UnresolvedRecovery(),
    )
    config = {"configurable": {"thread_id": str(uuid4())}}
    paused = await graph.ainvoke(
        {"incident_id": str(uuid4()), "service": "order-service", "symptom": "cache failed"},
        config=config,
    )
    result = await graph.ainvoke(
        Command(resume={"action_id": paused["remediation_plan"]["action_id"], "approved": True}),
        config=config,
    )
    assert result["execution"]["status"] == "completed"
    assert result["verification"]["status"] == "unresolved"
    assert result["error_code"] == "VERIFICATION_FAILED"


async def test_action_ledger_skips_operation_on_graph_replay() -> None:
    operations = Operations()
    ledger = InMemoryIncidentStore()
    graph = build_incident_graph(
        InvestigationCapabilities(Metrics(), Logs(), Traces()),
        checkpointer=InMemorySaver(),
        operations=operations,
        recovery=Recovery(),
        action_ledger=ledger,
    )
    incident_id = str(uuid4())
    results = []
    for _ in range(2):
        config = {"configurable": {"thread_id": str(uuid4())}}
        paused = await graph.ainvoke(
            {"incident_id": incident_id, "service": "order-service", "symptom": "cache failed"},
            config=config,
        )
        results.append(
            await graph.ainvoke(
                Command(
                    resume={"action_id": paused["remediation_plan"]["action_id"], "approved": True}
                ),
                config=config,
            )
        )
    assert len(operations.calls) == 1
    assert results[0]["execution"]["duplicate"] is False
    assert results[1]["execution"]["duplicate"] is True


async def test_graph_exports_real_parented_agent_and_tool_spans(
    monkeypatch: MonkeyPatch,
) -> None:
    provider = TracerProvider()
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    monkeypatch.setattr(trace, "get_tracer", provider.get_tracer)
    graph = build_incident_graph(
        InvestigationCapabilities(Metrics(), Logs(), Traces()),
        checkpointer=InMemorySaver(),
        operations=Operations(),
        recovery=Recovery(),
    )
    config = {"configurable": {"thread_id": str(uuid4())}}
    with provider.get_tracer("test").start_as_current_span("incident.run"):
        paused = await graph.ainvoke(
            {"incident_id": str(uuid4()), "service": "order-service", "symptom": "cache failed"},
            config=config,
        )
    with provider.get_tracer("test").start_as_current_span("incident.resume"):
        await graph.ainvoke(
            Command(
                resume={"action_id": paused["remediation_plan"]["action_id"], "approved": True}
            ),
            config=config,
        )

    spans = {span.name: span for span in exporter.get_finished_spans()}
    expected = {
        "incident.run",
        "incident.resume",
        "agent.supervisor.delegate",
        "agent.supervisor.fuse",
        "agent.metrics",
        "agent.logs",
        "agent.trace",
        "tool.query_service_metrics",
        "tool.query_recent_logs",
        "tool.query_service_traces",
        "agent.remediation",
        "tool.reset_redis_fault",
        "agent.verifier",
        "tool.probe_cache_recovery",
    }
    assert expected <= spans.keys()
    assert spans["agent.metrics"].parent.span_id == spans["incident.run"].context.span_id
    assert (
        spans["tool.query_service_metrics"].parent.span_id == spans["agent.metrics"].context.span_id
    )
    assert (
        spans["tool.reset_redis_fault"].parent.span_id == spans["operation.execute"].context.span_id
    )
    assert spans["agent.verifier"].parent.span_id == spans["incident.resume"].context.span_id
