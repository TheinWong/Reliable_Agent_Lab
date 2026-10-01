import asyncio

import pytest

from reliable_agent_lab.evidence import InvestigationCapabilities
from reliable_agent_lab.graph import build_incident_graph, merge_reports


class FakeMetrics:
    async def query_metrics(self, service: str) -> dict[str, object]:
        assert service == "order-service"
        return {"redisUnavailable": True, "cacheReadErrors": 1}


class FakeLogs:
    async def query_logs(self, service: str) -> dict[str, object]:
        assert service == "order-service"
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


async def test_graph_diagnoses_controlled_redis_fault() -> None:
    graph = build_incident_graph(fake_capabilities())

    result = await graph.ainvoke(
        {"incident_id": "test", "service": "order-service", "symptom": "cache failed"}
    )

    assert "Redis unavailability" in result["diagnosis"]
    assert [report["role"] for report in result["reports"]] == ["logs", "metrics", "trace"]
    assert result["reports"][2]["status"] == "unavailable"
    assert result["reports"][1]["evidence_refs"] == ["test:metrics"]


def test_reducer_replaces_replayed_role_report() -> None:
    original = [{"role": "metrics", "findings": ["old"]}]
    update = [{"role": "metrics", "findings": ["new"]}]
    assert merge_reports(original, update) == update
    assert original[0]["findings"] == ["old"]


async def test_specialists_start_in_parallel() -> None:
    started: set[str] = set()
    all_started = asyncio.Event()

    async def meet(role: str) -> None:
        started.add(role)
        if len(started) == 3:
            all_started.set()
        await asyncio.wait_for(all_started.wait(), timeout=1)

    class BarrierMetrics(FakeMetrics):
        async def query_metrics(self, service: str) -> dict[str, object]:
            await meet("metrics")
            return await super().query_metrics(service)

    class BarrierLogs(FakeLogs):
        async def query_logs(self, service: str) -> dict[str, object]:
            await meet("logs")
            return await super().query_logs(service)

    class BarrierTraces(FakeTraces):
        async def query_traces(self, service: str) -> dict[str, object]:
            await meet("trace")
            return await super().query_traces(service)

    graph = build_incident_graph(
        InvestigationCapabilities(BarrierMetrics(), BarrierLogs(), BarrierTraces())
    )
    result = await graph.ainvoke(
        {"incident_id": "parallel", "service": "order-service", "symptom": "cache failed"}
    )
    assert started == {"metrics", "logs", "trace"}
    assert result["error_code"] is None


async def test_failed_metrics_tool_remains_explicit() -> None:
    class BrokenMetrics:
        async def query_metrics(self, service: str) -> dict[str, object]:
            raise TimeoutError("simulated")

    graph = build_incident_graph(
        InvestigationCapabilities(BrokenMetrics(), FakeLogs(), FakeTraces())
    )
    result = await graph.ainvoke(
        {"incident_id": "failed", "service": "order-service", "symptom": "cache failed"}
    )
    assert result["error_code"] == "INSUFFICIENT_EVIDENCE"
    assert result["reports"][1]["error_code"] == "TOOL_TIMEOUT"


async def test_old_cache_failure_does_not_confirm_new_fault() -> None:
    class StaleLogs:
        async def query_logs(self, service: str) -> dict[str, object]:
            return {
                "events": [
                    {"type": "demo_fault_injected", "dependency": "redis"},
                    {"type": "order_cache_read_failed", "dependency": "redis"},
                    {"type": "demo_fault_reset", "dependency": "redis"},
                    {"type": "demo_fault_injected", "dependency": "redis"},
                ]
            }

    graph = build_incident_graph(
        InvestigationCapabilities(FakeMetrics(), StaleLogs(), FakeTraces())
    )
    result = await graph.ainvoke(
        {"incident_id": "stale", "service": "order-service", "symptom": "cache failed"}
    )
    assert result["error_code"] == "INSUFFICIENT_EVIDENCE"
    assert result["reports"][0]["hypotheses"] == []


async def test_graph_diagnoses_mysql_fault_only_with_matching_current_logs() -> None:
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

    graph = build_incident_graph(
        InvestigationCapabilities(MysqlMetrics(), MysqlLogs(), FakeTraces())
    )
    result = await graph.ainvoke(
        {"incident_id": "s2", "service": "order-service", "symptom": "uncached order 503"}
    )
    assert "MySQL unavailability" in result["diagnosis"]
    assert result["error_code"] is None


async def test_graph_rejects_ambiguous_concurrent_mysql_and_redis_faults() -> None:
    class BothMetrics:
        async def query_metrics(self, service: str) -> dict[str, object]:
            return {"redisUnavailable": True, "mysqlUnavailable": True}

    graph = build_incident_graph(InvestigationCapabilities(BothMetrics(), FakeLogs(), FakeTraces()))
    result = await graph.ainvoke(
        {"incident_id": "both", "service": "order-service", "symptom": "dependencies failed"}
    )
    assert result["error_code"] == "INSUFFICIENT_EVIDENCE"


@pytest.mark.parametrize(
    ("kind", "fresh_log", "fresh_span", "expected"),
    [
        ("inventory", True, True, True),
        ("inventory", False, True, False),
        ("inventory", True, False, False),
        ("payment", True, True, True),
        ("payment", False, True, False),
        ("payment", True, False, False),
    ],
)
async def test_downstream_diagnosis_requires_post_injection_log_and_real_span(
    kind: str, fresh_log: bool, fresh_span: bool, expected: bool
) -> None:
    is_inventory = kind == "inventory"
    started = "2026-10-01T12:00:00Z"
    start_ns = 1790856000000000000
    event_type = "order_inventory_slow" if is_inventory else "order_payment_request_failed"
    span_name = (
        "GET /api/inventory/{sku}" if is_inventory else "GET /api/payments/authorization-preview"
    )

    class DownstreamMetrics:
        async def query_metrics(self, service: str) -> dict[str, object]:
            return {
                "redisUnavailable": False,
                "mysqlUnavailable": False,
                "inventoryLatencyActive": is_inventory,
                "inventoryFaultStartedAt": started if is_inventory else "",
                "paymentHttp5xxActive": not is_inventory,
                "paymentFaultStartedAt": started if not is_inventory else "",
            }

    class DownstreamLogs:
        async def query_logs(self, service: str) -> dict[str, object]:
            return {
                "events": [
                    {
                        "type": event_type,
                        "dependency": kind,
                        "observedAt": "2026-10-01T12:00:01Z"
                        if fresh_log
                        else "2026-10-01T11:59:59Z",
                    }
                ]
            }

    class DownstreamTraces:
        async def query_traces(self, service: str) -> dict[str, object]:
            return {
                "available": True,
                "spans": [
                    {
                        "service": "inventory-service" if is_inventory else "payment-service",
                        "name": span_name,
                        "start_time_unix_nano": str(
                            start_ns + 1_000_000_000 if fresh_span else start_ns - 1_000_000_000
                        ),
                        "duration_ms": "800" if is_inventory else "20",
                        "http_status": "200" if is_inventory else "503",
                    }
                ],
            }

    graph = build_incident_graph(
        InvestigationCapabilities(DownstreamMetrics(), DownstreamLogs(), DownstreamTraces())
    )
    result = await graph.ainvoke(
        {
            "incident_id": f"{kind}-{fresh_log}-{fresh_span}",
            "service": "order-service",
            "symptom": "checkout preview degraded",
        }
    )
    assert (result["error_code"] is None) is expected
    if expected:
        assert kind in result["diagnosis"]
    else:
        assert result["error_code"] == "INSUFFICIENT_EVIDENCE"
