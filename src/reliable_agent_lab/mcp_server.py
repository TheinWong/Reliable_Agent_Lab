import argparse
import asyncio
import os
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID

import httpx
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import ValidationError

from reliable_agent_lab.mcp_contracts import (
    CacheRecoveryProbe,
    DownstreamRecoveryProbe,
    LogsSnapshot,
    MetricsSnapshot,
    ResetFaultResult,
    ToolErrorCode,
    TraceSnapshot,
)


class DemoServiceReader:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)

    async def get(self, path: str) -> dict[str, object]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}{path}")
                response.raise_for_status()
                result: dict[str, object] = response.json()
                return result
        except httpx.TimeoutException as exc:
            raise ToolError(f"{ToolErrorCode.TIMEOUT}: service timed out") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ToolError(f"{ToolErrorCode.DEPENDENCY}: service unavailable") from exc

    async def reset_redis_fault(self, traceparent: str | None = None) -> bool:
        return await self._reset_fault("redis", traceparent)

    async def reset_mysql_fault(self, traceparent: str | None = None) -> bool:
        return await self._reset_fault("mysql", traceparent)

    async def reset_inventory_latency(self, traceparent: str | None = None) -> bool:
        return await self._reset_fault("inventory", traceparent)

    async def reset_payment_5xx(self, traceparent: str | None = None) -> bool:
        return await self._reset_fault("payment", traceparent)

    async def _reset_fault(
        self, dependency: Literal["redis", "mysql", "inventory", "payment"], traceparent: str | None
    ) -> bool:
        paths = {
            "redis": ("/internal/faults/redis-unavailable", "redisUnavailable"),
            "mysql": ("/internal/faults/mysql-unavailable", "mysqlUnavailable"),
            "inventory": ("/internal/faults/inventory-latency", "inventoryLatency"),
            "payment": ("/internal/faults/payment-5xx", "paymentHttp5xx"),
        }
        path, field = paths[dependency]
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.delete(
                    f"{self._base_url}{path}",
                    headers={"traceparent": traceparent} if traceparent else None,
                )
                response.raise_for_status()
                value: dict[str, object] = response.json()
                return value.get(field) is True
        except httpx.TimeoutException as exc:
            raise ToolError(f"{ToolErrorCode.TIMEOUT}: reset timed out") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise ToolError(f"{ToolErrorCode.OPERATION}: reset failed") from exc


class JaegerTraceReader:
    """Read a small recent window from Jaeger's documented v3 query API."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)
        self._transport = transport

    async def query(self) -> TraceSnapshot:
        now = datetime.now(UTC)
        base_params: dict[str, str | int] = {
            "query.serviceName": "order-service",
            "query.startTimeMin": (now - timedelta(minutes=10)).isoformat(),
            "query.startTimeMax": now.isoformat(),
            "query.searchDepth": 5,
            "query.pagination.pageSize": 5,
        }
        try:
            spans_by_identity: dict[tuple[str, str], dict[str, str]] = {}
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                for operation in (
                    "GET /api/orders/{id}/checkout-preview",
                    "GET /api/orders/{id}",
                ):
                    params = {**base_params, "query.operationName": operation}
                    async with client.stream(
                        "GET", f"{self._base_url}/api/v3/traces", params=params
                    ) as response:
                        if response.status_code == 404:
                            continue
                        response.raise_for_status()
                        chunks = bytearray()
                        async for chunk in response.aiter_bytes():
                            chunks.extend(chunk)
                            if len(chunks) > 1_000_000:
                                raise ValueError("Jaeger response exceeded limit")
                    data = httpx.Response(200, content=bytes(chunks)).json()
                    resource_spans = data["result"]["resourceSpans"]
                    if not isinstance(resource_spans, list):
                        raise ValueError("invalid Jaeger resourceSpans")
                    for resource_group in resource_spans[:20]:
                        resource_attributes = resource_group.get("resource", {}).get(
                            "attributes", []
                        )
                        service = next(
                            (
                                attribute.get("value", {}).get("stringValue")
                                for attribute in resource_attributes
                                if attribute.get("key") == "service.name"
                            ),
                            None,
                        )
                        if service not in {
                            "order-service",
                            "inventory-service",
                            "payment-service",
                        }:
                            continue
                        for scope_group in resource_group.get("scopeSpans", [])[:10]:
                            for item in scope_group.get("spans", [])[:30]:
                                trace_id = item.get("traceId")
                                span_id = item.get("spanId")
                                name = item.get("name")
                                start = item.get("startTimeUnixNano")
                                end = item.get("endTimeUnixNano")
                                if not all(
                                    isinstance(value, str)
                                    for value in (trace_id, span_id, name, start, end)
                                ):
                                    continue
                                span_attributes = item.get("attributes", [])
                                status_code = next(
                                    (
                                        attribute.get("value", {}).get("intValue", "")
                                        for attribute in span_attributes
                                        if attribute.get("key") == "http.response.status_code"
                                    ),
                                    "",
                                )
                                spans_by_identity[(trace_id, span_id)] = {
                                    "trace_id": trace_id,
                                    "span_id": span_id,
                                    "name": name[:120],
                                    "start_time_unix_nano": start,
                                    "duration_ms": str(
                                        max(0, (int(end) - int(start)) // 1_000_000)
                                    ),
                                    "http_status": str(status_code),
                                    "service": service,
                                    "provenance": "jaeger:/api/v3/traces",
                                }
            spans = sorted(
                spans_by_identity.values(),
                key=lambda item: int(item["start_time_unix_nano"]),
                reverse=True,
            )[:20]
            return TraceSnapshot(
                available=True,
                reason="" if spans else "no recent order-service spans",
                spans=spans,
            )
        except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError) as exc:
            return TraceSnapshot(
                available=False, reason=f"Jaeger query unavailable: {type(exc).__name__}"
            )


def build_metrics_server(
    reader: DemoServiceReader,
    inventory_reader: DemoServiceReader | None = None,
    payment_reader: DemoServiceReader | None = None,
) -> MCPServer:
    server = MCPServer("observability-metrics")

    @server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def query_service_metrics(service: Literal["order-service"]) -> MetricsSnapshot:
        """Read bounded order metrics and current local downstream fault states."""
        try:
            payload = await reader.get("/internal/evidence/metrics")
            if inventory_reader is not None:
                inventory = await inventory_reader.get("/internal/faults")
                payload["inventoryLatencyActive"] = inventory["inventoryLatency"]
                payload["inventoryFaultStartedAt"] = inventory["faultStartedAt"]
            if payment_reader is not None:
                payment = await payment_reader.get("/internal/faults")
                payload["paymentHttp5xxActive"] = payment["paymentHttp5xx"]
                payload["paymentFaultStartedAt"] = payment["faultStartedAt"]
            return MetricsSnapshot.model_validate(payload)
        except (KeyError, ValidationError) as exc:
            raise ToolError(f"{ToolErrorCode.DEPENDENCY}: invalid metrics payload") from exc

    @server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def probe_cache_recovery(service: Literal["order-service"]) -> CacheRecoveryProbe:
        """Read fault state and two order responses to independently check cache recovery."""
        try:
            fault = await reader.get("/internal/faults")
            first = await reader.get("/api/orders/1")
            second = await reader.get("/api/orders/1")
            return CacheRecoveryProbe.model_validate(
                {
                    "service": service,
                    "fault_cleared": fault["redisUnavailable"] is False,
                    "first_source": first["source"],
                    "second_source": second["source"],
                }
            )
        except (KeyError, ValidationError) as exc:
            raise ToolError(f"{ToolErrorCode.DEPENDENCY}: invalid recovery payload") from exc

    @server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def probe_mysql_recovery(service: Literal["order-service"]) -> CacheRecoveryProbe:
        """Check cleared MySQL fault using a fresh database read and later cache hit."""
        try:
            fault = await reader.get("/internal/faults")
            first = await reader.get("/api/orders/1")
            second = await reader.get("/api/orders/1")
            return CacheRecoveryProbe.model_validate(
                {
                    "service": service,
                    "fault_cleared": fault["mysqlUnavailable"] is False,
                    "first_source": first["source"],
                    "second_source": second["source"],
                }
            )
        except (KeyError, ValidationError) as exc:
            raise ToolError(f"{ToolErrorCode.DEPENDENCY}: invalid MySQL recovery payload") from exc

    async def downstream_probe(
        service: Literal["order-service"],
        downstream_reader: DemoServiceReader | None,
        fault_field: str,
    ) -> DownstreamRecoveryProbe:
        if downstream_reader is None:
            raise ToolError(f"{ToolErrorCode.DEPENDENCY}: downstream reader unavailable")
        try:
            fault = await downstream_reader.get("/internal/faults")
            preview = await reader.get("/api/orders/1/checkout-preview")
            return DownstreamRecoveryProbe.model_validate(
                {
                    "service": service,
                    "fault_cleared": fault[fault_field] is False,
                    "preview_status": preview["status"],
                    "inventory_latency_ms": preview["inventoryLatencyMs"],
                    "payment_authorized": preview["paymentAuthorized"],
                }
            )
        except (KeyError, ValidationError) as exc:
            raise ToolError(
                f"{ToolErrorCode.DEPENDENCY}: invalid downstream recovery payload"
            ) from exc

    @server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def probe_inventory_recovery(
        service: Literal["order-service"],
    ) -> DownstreamRecoveryProbe:
        """Verify inventory fault state and a fresh checkout preview."""
        return await downstream_probe(service, inventory_reader, "inventoryLatency")

    @server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def probe_payment_recovery(
        service: Literal["order-service"],
    ) -> DownstreamRecoveryProbe:
        """Verify payment fault state and a fresh checkout preview."""
        return await downstream_probe(service, payment_reader, "paymentHttp5xx")

    return server


def build_logs_server(reader: DemoServiceReader) -> MCPServer:
    server = MCPServer("observability-logs")

    @server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def query_recent_logs(service: Literal["order-service"]) -> LogsSnapshot:
        """Read the bounded structured demo event buffer, never arbitrary host logs."""
        try:
            return LogsSnapshot.model_validate(await reader.get("/internal/evidence/logs"))
        except ValidationError as exc:
            raise ToolError(f"{ToolErrorCode.DEPENDENCY}: invalid logs payload") from exc

    return server


def build_traces_server(reader: JaegerTraceReader | None = None) -> MCPServer:
    server = MCPServer("observability-traces")

    @server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    async def query_service_traces(service: Literal["order-service"]) -> TraceSnapshot:
        """Read bounded recent order-service spans from Jaeger, without synthetic data."""
        if reader is None:
            return TraceSnapshot(available=False, reason="trace backend is not configured")
        return await reader.query()

    return server


class ResetLedger:
    """Process-local duplicate guard; Java reset remains idempotent across restarts."""

    def __init__(self) -> None:
        self._completed: dict[tuple[str, UUID], ResetFaultResult] = {}
        self._lock = asyncio.Lock()

    async def reset(
        self,
        action_id: UUID,
        reader: DemoServiceReader,
        dependency: Literal["redis", "mysql", "inventory", "payment"],
        traceparent: str | None,
    ) -> ResetFaultResult:
        async with self._lock:
            key = (dependency, action_id)
            previous = self._completed.get(key)
            if previous is not None:
                return previous.model_copy(update={"duplicate": True})
            reset = {
                "redis": reader.reset_redis_fault,
                "mysql": reader.reset_mysql_fault,
                "inventory": reader.reset_inventory_latency,
                "payment": reader.reset_payment_5xx,
            }[dependency]
            still_unavailable = await reset(traceparent)
            result = ResetFaultResult(
                action_id=action_id,
                scope="local-demo",
                redis_unavailable=still_unavailable if dependency == "redis" else False,
                mysql_unavailable=still_unavailable if dependency == "mysql" else False,
                inventory_latency=still_unavailable if dependency == "inventory" else False,
                payment_http5xx=still_unavailable if dependency == "payment" else False,
            )
            self._completed[key] = result
            return result


def build_operations_server(
    reader: DemoServiceReader,
    enabled: bool,
    inventory_reader: DemoServiceReader | None = None,
    payment_reader: DemoServiceReader | None = None,
) -> MCPServer:
    server = MCPServer("demo-operations")
    ledger = ResetLedger()

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        )
    )
    async def reset_redis_fault(
        action_id: UUID, scope: Literal["local-demo"], traceparent: str | None = None
    ) -> ResetFaultResult:
        """Reset only the controlled Redis fault in this local demo environment."""
        if not enabled:
            raise ToolError(f"{ToolErrorCode.POLICY}: operations server is disabled")
        if scope != "local-demo":
            raise ToolError(f"{ToolErrorCode.POLICY}: invalid scope")
        if (
            traceparent is not None
            and re.fullmatch(r"00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}", traceparent) is None
        ):
            raise ToolError(f"{ToolErrorCode.VALIDATION}: invalid traceparent")
        return await ledger.reset(action_id, reader, "redis", traceparent)

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        )
    )
    async def reset_mysql_fault(
        action_id: UUID, scope: Literal["local-demo"], traceparent: str | None = None
    ) -> ResetFaultResult:
        """Reset only the controlled MySQL read fault in this local demo environment."""
        if not enabled:
            raise ToolError(f"{ToolErrorCode.POLICY}: operations server is disabled")
        if scope != "local-demo":
            raise ToolError(f"{ToolErrorCode.POLICY}: invalid scope")
        if (
            traceparent is not None
            and re.fullmatch(r"00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}", traceparent) is None
        ):
            raise ToolError(f"{ToolErrorCode.VALIDATION}: invalid traceparent")
        return await ledger.reset(action_id, reader, "mysql", traceparent)

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        )
    )
    async def reset_inventory_latency(
        action_id: UUID, scope: Literal["local-demo"], traceparent: str | None = None
    ) -> ResetFaultResult:
        """Reset only the controlled inventory latency fault."""
        if not enabled or scope != "local-demo":
            raise ToolError(f"{ToolErrorCode.POLICY}: operation is disabled or scope invalid")
        if (
            traceparent is not None
            and re.fullmatch(r"00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}", traceparent) is None
        ):
            raise ToolError(f"{ToolErrorCode.VALIDATION}: invalid traceparent")
        if inventory_reader is None:
            raise ToolError(f"{ToolErrorCode.DEPENDENCY}: inventory reader unavailable")
        return await ledger.reset(action_id, inventory_reader, "inventory", traceparent)

    @server.tool(
        annotations=ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
            idempotent_hint=True,
            open_world_hint=False,
        )
    )
    async def reset_payment_5xx(
        action_id: UUID, scope: Literal["local-demo"], traceparent: str | None = None
    ) -> ResetFaultResult:
        """Reset only the controlled payment HTTP 5xx fault."""
        if not enabled or scope != "local-demo":
            raise ToolError(f"{ToolErrorCode.POLICY}: operation is disabled or scope invalid")
        if (
            traceparent is not None
            and re.fullmatch(r"00-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}", traceparent) is None
        ):
            raise ToolError(f"{ToolErrorCode.VALIDATION}: invalid traceparent")
        if payment_reader is None:
            raise ToolError(f"{ToolErrorCode.DEPENDENCY}: payment reader unavailable")
        return await ledger.reset(action_id, payment_reader, "payment", traceparent)

    return server


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("group", choices=("metrics", "logs", "traces", "operations"))
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    reader = DemoServiceReader(
        os.getenv("RAL_ORDER_SERVICE_URL", "http://order-service:8080"),
        float(os.getenv("RAL_TOOL_TIMEOUT_SECONDS", "5")),
    )
    inventory_reader = DemoServiceReader(
        os.getenv("RAL_INVENTORY_SERVICE_URL", "http://inventory-service:8080"),
        float(os.getenv("RAL_TOOL_TIMEOUT_SECONDS", "5")),
    )
    payment_reader = DemoServiceReader(
        os.getenv("RAL_PAYMENT_SERVICE_URL", "http://payment-service:8080"),
        float(os.getenv("RAL_TOOL_TIMEOUT_SECONDS", "5")),
    )
    servers: dict[str, Callable[[], MCPServer]] = {
        "metrics": lambda: build_metrics_server(reader, inventory_reader, payment_reader),
        "logs": lambda: build_logs_server(reader),
        "traces": lambda: build_traces_server(
            JaegerTraceReader(
                os.getenv("RAL_JAEGER_QUERY_URL", "http://jaeger:16686"),
                float(os.getenv("RAL_TOOL_TIMEOUT_SECONDS", "5")),
            )
        ),
        "operations": lambda: build_operations_server(
            reader,
            os.getenv("RAL_DEMO_OPERATIONS_ENABLED") == "true",
            inventory_reader,
            payment_reader,
        ),
    }
    servers[args.group]().run(
        transport="streamable-http",
        host="0.0.0.0",
        port=args.port,
        json_response=True,
        stateless_http=True,
    )


if __name__ == "__main__":
    main()
