import asyncio
from dataclasses import dataclass
from typing import Any, Protocol

from mcp import Client
from mcp.server import MCPServer
from mcp.types import TextContent
from pydantic import ValidationError

from reliable_agent_lab.mcp_contracts import (
    CacheRecoveryProbe,
    CapabilityError,
    DownstreamRecoveryProbe,
    LogsSnapshot,
    MetricsSnapshot,
    ToolErrorCode,
    TraceSnapshot,
)


class MetricsCapability(Protocol):
    async def query_metrics(self, service: str) -> dict[str, Any]: ...


class LogsCapability(Protocol):
    async def query_logs(self, service: str) -> dict[str, Any]: ...


class TraceCapability(Protocol):
    async def query_traces(self, service: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class InvestigationCapabilities:
    metrics: MetricsCapability
    logs: LogsCapability
    traces: TraceCapability


class _MCPReadOnlyClient:
    def __init__(self, target: str | MCPServer, timeout_seconds: float) -> None:
        self._target = target
        self._timeout_seconds = timeout_seconds

    async def _call(self, tool_name: str, service: str) -> dict[str, Any]:
        if service != "order-service":
            raise CapabilityError(ToolErrorCode.VALIDATION, "unsupported service")
        try:
            async with asyncio.timeout(self._timeout_seconds):
                async with Client(
                    self._target, read_timeout_seconds=self._timeout_seconds
                ) as client:
                    result = await client.call_tool(tool_name, {"service": service})
        except TimeoutError as exc:
            raise CapabilityError(ToolErrorCode.TIMEOUT, "MCP call timed out") from exc
        except CapabilityError:
            raise
        except Exception as exc:
            raise CapabilityError(ToolErrorCode.DEPENDENCY, "MCP server unavailable") from exc
        if result.is_error:
            message = next(
                (block.text for block in result.content if isinstance(block, TextContent)),
                "MCP tool failed",
            )
            code = next(
                (item for item in ToolErrorCode if item.value in message),
                ToolErrorCode.OPERATION,
            )
            raise CapabilityError(code, message[:200])
        if not isinstance(result.structured_content, dict):
            raise CapabilityError(ToolErrorCode.DEPENDENCY, "MCP tool returned no typed payload")
        return result.structured_content


class MCPMetricsClient(_MCPReadOnlyClient):
    async def query_metrics(self, service: str) -> dict[str, Any]:
        payload = await self._call("query_service_metrics", service)
        try:
            return MetricsSnapshot.model_validate(payload).model_dump(by_alias=True)
        except ValidationError as exc:
            raise CapabilityError(ToolErrorCode.DEPENDENCY, "invalid metrics payload") from exc


class MCPRecoveryClient(_MCPReadOnlyClient):
    async def probe_recovery(self, service: str) -> CacheRecoveryProbe:
        payload = await self._call("probe_cache_recovery", service)
        try:
            return CacheRecoveryProbe.model_validate(payload)
        except ValidationError as exc:
            raise CapabilityError(ToolErrorCode.DEPENDENCY, "invalid recovery payload") from exc

    async def probe_mysql_recovery(self, service: str) -> CacheRecoveryProbe:
        payload = await self._call("probe_mysql_recovery", service)
        try:
            return CacheRecoveryProbe.model_validate(payload)
        except ValidationError as exc:
            raise CapabilityError(
                ToolErrorCode.DEPENDENCY, "invalid MySQL recovery payload"
            ) from exc

    async def probe_inventory_recovery(self, service: str) -> DownstreamRecoveryProbe:
        return await self._probe_downstream("probe_inventory_recovery", service)

    async def probe_payment_recovery(self, service: str) -> DownstreamRecoveryProbe:
        return await self._probe_downstream("probe_payment_recovery", service)

    async def _probe_downstream(self, tool: str, service: str) -> DownstreamRecoveryProbe:
        payload = await self._call(tool, service)
        try:
            return DownstreamRecoveryProbe.model_validate(payload)
        except ValidationError as exc:
            raise CapabilityError(
                ToolErrorCode.DEPENDENCY, "invalid downstream recovery payload"
            ) from exc


class MCPLogsClient(_MCPReadOnlyClient):
    async def query_logs(self, service: str) -> dict[str, Any]:
        payload = await self._call("query_recent_logs", service)
        try:
            return LogsSnapshot.model_validate(payload).model_dump(mode="json", by_alias=True)
        except ValidationError as exc:
            raise CapabilityError(ToolErrorCode.DEPENDENCY, "invalid logs payload") from exc


class MCPTracesClient(_MCPReadOnlyClient):
    async def query_traces(self, service: str) -> dict[str, Any]:
        payload = await self._call("query_service_traces", service)
        try:
            return TraceSnapshot.model_validate(payload).model_dump(mode="json")
        except ValidationError as exc:
            raise CapabilityError(ToolErrorCode.DEPENDENCY, "invalid traces payload") from exc


def mcp_investigation_capabilities(
    metrics_url: str,
    logs_url: str,
    traces_url: str,
    timeout_seconds: float,
) -> InvestigationCapabilities:
    return InvestigationCapabilities(
        metrics=MCPMetricsClient(metrics_url, timeout_seconds),
        logs=MCPLogsClient(logs_url, timeout_seconds),
        traces=MCPTracesClient(traces_url, timeout_seconds),
    )
