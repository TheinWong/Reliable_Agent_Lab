from uuid import uuid4

import httpx
import pytest
from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError

from reliable_agent_lab.evidence import (
    MCPLogsClient,
    MCPMetricsClient,
    MCPRecoveryClient,
    MCPTracesClient,
)
from reliable_agent_lab.mcp_contracts import CapabilityError, ToolErrorCode
from reliable_agent_lab.mcp_server import (
    DemoServiceReader,
    JaegerTraceReader,
    build_logs_server,
    build_metrics_server,
    build_operations_server,
    build_traces_server,
)


class FakeReader(DemoServiceReader):
    def __init__(self) -> None:
        self.reset_calls = 0
        self.last_traceparent: str | None = None

    async def get(self, path: str) -> dict[str, object]:
        if path.endswith("metrics"):
            return {
                "service": "order-service",
                "redisUnavailable": True,
                "cacheReadErrors": 1,
                "mysqlCacheErrorFallbacks": 1,
            }
        return {
            "events": [
                {
                    "observedAt": "2026-09-30T00:00:00Z",
                    "type": "order_cache_read_failed",
                    "dependency": "redis",
                    "detail": "IllegalStateException",
                }
            ]
        }

    async def reset_redis_fault(self, traceparent: str | None = None) -> bool:
        self.reset_calls += 1
        self.last_traceparent = traceparent
        return False

    async def reset_mysql_fault(self, traceparent: str | None = None) -> bool:
        self.reset_calls += 1
        self.last_traceparent = traceparent
        return False


async def test_read_only_mcp_groups_have_distinct_tool_lists_and_typed_results() -> None:
    reader = FakeReader()
    servers = {
        "metrics": build_metrics_server(reader),
        "logs": build_logs_server(reader),
        "traces": build_traces_server(),
    }
    expected = {
        "metrics": {
            "query_service_metrics",
            "probe_cache_recovery",
            "probe_mysql_recovery",
            "probe_inventory_recovery",
            "probe_payment_recovery",
        },
        "logs": {"query_recent_logs"},
        "traces": {"query_service_traces"},
    }
    for role, server in servers.items():
        async with Client(server) as client:
            tools = (await client.list_tools()).tools
            assert {tool.name for tool in tools} == expected[role]
            assert all(tool.annotations is not None for tool in tools)
            assert all(
                tool.annotations.read_only_hint is True for tool in tools if tool.annotations
            )

    metrics = await MCPMetricsClient(servers["metrics"], 5).query_metrics("order-service")
    logs = await MCPLogsClient(servers["logs"], 5).query_logs("order-service")
    traces = await MCPTracesClient(servers["traces"], 5).query_traces("order-service")
    assert metrics["redisUnavailable"] is True
    assert logs["events"][0]["type"] == "order_cache_read_failed"
    assert traces["available"] is False
    assert traces["spans"] == []


async def test_invalid_service_is_rejected_before_tool_call() -> None:
    client = MCPMetricsClient(build_metrics_server(FakeReader()), 5)
    with pytest.raises(CapabilityError) as error:
        await client.query_metrics("other-service")
    assert error.value.code == ToolErrorCode.VALIDATION


async def test_operations_tool_is_scoped_and_idempotent() -> None:
    reader = FakeReader()
    server = build_operations_server(reader, enabled=True)
    action_id = str(uuid4())
    async with Client(server) as client:
        tools = (await client.list_tools()).tools
        assert {tool.name for tool in tools} == {
            "reset_redis_fault",
            "reset_mysql_fault",
            "reset_inventory_latency",
            "reset_payment_5xx",
        }
        assert tools[0].annotations is not None
        assert tools[0].annotations.read_only_hint is False
        assert tools[0].annotations.idempotent_hint is True
        first = await client.call_tool(
            "reset_redis_fault", {"action_id": action_id, "scope": "local-demo"}
        )
        second = await client.call_tool(
            "reset_redis_fault", {"action_id": action_id, "scope": "local-demo"}
        )
        invalid = await client.call_tool(
            "reset_redis_fault", {"action_id": action_id, "scope": "production"}
        )
        malformed_trace = await client.call_tool(
            "reset_redis_fault",
            {"action_id": str(uuid4()), "scope": "local-demo", "traceparent": "bad"},
        )
    assert first.is_error is False
    assert second.is_error is False
    assert first.structured_content["duplicate"] is False
    assert second.structured_content["duplicate"] is True
    assert reader.reset_calls == 1
    assert invalid.is_error is True
    assert malformed_trace.is_error is True
    assert reader.last_traceparent is None


async def test_operations_server_disabled_by_default() -> None:
    reader = FakeReader()
    server = build_operations_server(reader, enabled=False)
    async with Client(server) as client:
        result = await client.call_tool(
            "reset_redis_fault", {"action_id": str(uuid4()), "scope": "local-demo"}
        )
    assert result.is_error is True
    assert reader.reset_calls == 0


async def test_mysql_reset_is_scoped_and_idempotent() -> None:
    reader = FakeReader()
    server = build_operations_server(reader, enabled=True)
    action_id = str(uuid4())
    async with Client(server) as client:
        first = await client.call_tool(
            "reset_mysql_fault", {"action_id": action_id, "scope": "local-demo"}
        )
        second = await client.call_tool(
            "reset_mysql_fault", {"action_id": action_id, "scope": "local-demo"}
        )
    assert first.is_error is False
    assert second.is_error is False
    assert first.structured_content["mysql_unavailable"] is False
    assert first.structured_content["duplicate"] is False
    assert second.structured_content["duplicate"] is True
    assert reader.reset_calls == 1


async def test_tool_timeout_is_not_reported_as_empty_metrics() -> None:
    class TimeoutReader(FakeReader):
        async def get(self, path: str) -> dict[str, object]:
            raise ToolError("TOOL_TIMEOUT: order-service timed out")

    client = MCPMetricsClient(build_metrics_server(TimeoutReader()), 5)
    with pytest.raises(CapabilityError) as error:
        await client.query_metrics("order-service")
    assert error.value.code == ToolErrorCode.TIMEOUT


async def test_empty_logs_are_valid_but_not_a_failure_pattern() -> None:
    class EmptyReader(FakeReader):
        async def get(self, path: str) -> dict[str, object]:
            return {"events": []}

    logs = await MCPLogsClient(build_logs_server(EmptyReader()), 5).query_logs("order-service")
    assert logs == {"events": []}


async def test_invalid_downstream_payload_is_dependency_failure() -> None:
    class InvalidReader(FakeReader):
        async def get(self, path: str) -> dict[str, object]:
            return {"service": "order-service", "cacheReadErrors": -1}

    client = MCPMetricsClient(build_metrics_server(InvalidReader()), 5)
    with pytest.raises(CapabilityError) as error:
        await client.query_metrics("order-service")
    assert error.value.code == ToolErrorCode.DEPENDENCY


async def test_verifier_probe_uses_fresh_reads() -> None:
    paths: list[str] = []

    class RecoveryReader(FakeReader):
        async def get(self, path: str) -> dict[str, object]:
            paths.append(path)
            if path == "/internal/faults":
                return {"redisUnavailable": False}
            return {"source": "DATABASE" if paths.count(path) == 1 else "CACHE"}

    probe = await MCPRecoveryClient(build_metrics_server(RecoveryReader()), 5).probe_recovery(
        "order-service"
    )
    assert paths == ["/internal/faults", "/api/orders/1", "/api/orders/1"]
    assert probe.fault_cleared
    assert probe.first_source == "DATABASE"
    assert probe.second_source == "CACHE"


async def test_downstream_metrics_recovery_and_scoped_reset_tools() -> None:
    class OrderReader(FakeReader):
        async def get(self, path: str) -> dict[str, object]:
            if path == "/internal/evidence/metrics":
                return await super().get(path)
            if path == "/api/orders/1/checkout-preview":
                return {"status": "OK", "inventoryLatencyMs": 24, "paymentAuthorized": True}
            raise AssertionError(path)

    class DownstreamReader(FakeReader):
        def __init__(self, dependency: str) -> None:
            super().__init__()
            self.dependency = dependency

        async def get(self, path: str) -> dict[str, object]:
            assert path == "/internal/faults"
            if self.dependency == "inventory":
                return {"inventoryLatency": False, "faultStartedAt": ""}
            return {"paymentHttp5xx": False, "faultStartedAt": ""}

        async def reset_inventory_latency(self, traceparent: str | None = None) -> bool:
            self.reset_calls += 1
            return False

        async def reset_payment_5xx(self, traceparent: str | None = None) -> bool:
            self.reset_calls += 1
            return False

    order = OrderReader()
    inventory = DownstreamReader("inventory")
    payment = DownstreamReader("payment")
    metrics_server = build_metrics_server(order, inventory, payment)
    snapshot = await MCPMetricsClient(metrics_server, 5).query_metrics("order-service")
    assert snapshot["inventoryLatencyActive"] is False
    assert snapshot["paymentHttp5xxActive"] is False
    recovery = MCPRecoveryClient(metrics_server, 5)
    inventory_probe = await recovery.probe_inventory_recovery("order-service")
    payment_probe = await recovery.probe_payment_recovery("order-service")
    assert inventory_probe.fault_cleared and payment_probe.fault_cleared
    assert inventory_probe.inventory_latency_ms == 24
    assert payment_probe.payment_authorized

    server = build_operations_server(order, True, inventory, payment)
    action_id = str(uuid4())
    async with Client(server) as client:
        first = await client.call_tool(
            "reset_inventory_latency", {"action_id": action_id, "scope": "local-demo"}
        )
        duplicate = await client.call_tool(
            "reset_inventory_latency", {"action_id": action_id, "scope": "local-demo"}
        )
        other = await client.call_tool(
            "reset_payment_5xx", {"action_id": action_id, "scope": "local-demo"}
        )
        denied = await client.call_tool(
            "reset_payment_5xx", {"action_id": str(uuid4()), "scope": "production"}
        )
    assert first.structured_content["duplicate"] is False
    assert duplicate.structured_content["duplicate"] is True
    assert other.structured_content["duplicate"] is False
    assert inventory.reset_calls == payment.reset_calls == 1
    assert denied.is_error


async def test_jaeger_reader_returns_only_bounded_real_service_spans() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v3/traces"
        assert request.url.params["query.serviceName"] == "order-service"
        assert request.url.params["query.operationName"] in {
            "GET /api/orders/{id}",
            "GET /api/orders/{id}/checkout-preview",
        }
        assert request.url.params["query.pagination.pageSize"] == "5"
        return httpx.Response(
            200,
            json={
                "result": {
                    "resourceSpans": [
                        {
                            "resource": {
                                "attributes": [
                                    {
                                        "key": "service.name",
                                        "value": {"stringValue": "order-service"},
                                    }
                                ]
                            },
                            "scopeSpans": [
                                {
                                    "spans": [
                                        {
                                            "traceId": "a" * 32,
                                            "spanId": "b" * 16,
                                            "name": "GET /api/orders/{id}",
                                            "startTimeUnixNano": "123",
                                            "endTimeUnixNano": "124",
                                        }
                                    ]
                                }
                            ],
                        },
                        {
                            "resource": {
                                "attributes": [
                                    {"key": "service.name", "value": {"stringValue": "other"}}
                                ]
                            },
                            "scopeSpans": [
                                {
                                    "spans": [
                                        {
                                            "traceId": "c" * 32,
                                            "spanId": "d" * 16,
                                            "name": "not-order",
                                            "startTimeUnixNano": "456",
                                        }
                                    ]
                                }
                            ],
                        },
                    ]
                }
            },
        )

    reader = JaegerTraceReader("http://jaeger:16686", 5, httpx.MockTransport(handler))
    snapshot = await reader.query()
    assert snapshot.available is True
    assert len(snapshot.spans) == 1
    assert snapshot.spans[0]["trace_id"] == "a" * 32
    assert snapshot.spans[0]["provenance"] == "jaeger:/api/v3/traces"


async def test_jaeger_reader_distinguishes_empty_and_unavailable() -> None:
    empty = JaegerTraceReader(
        "http://jaeger:16686",
        5,
        httpx.MockTransport(lambda _: httpx.Response(200, json={"result": {"resourceSpans": []}})),
    )
    unavailable = JaegerTraceReader(
        "http://jaeger:16686", 5, httpx.MockTransport(lambda _: httpx.Response(503))
    )
    empty_result = await empty.query()
    unavailable_result = await unavailable.query()
    assert empty_result.available is True
    assert empty_result.spans == []
    assert empty_result.reason == "no recent order-service spans"
    assert unavailable_result.available is False
    assert unavailable_result.spans == []
