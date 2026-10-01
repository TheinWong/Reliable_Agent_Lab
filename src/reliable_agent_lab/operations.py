"""Approval-only client for the constrained operations MCP server."""

import asyncio
from typing import Protocol
from uuid import UUID

from mcp import Client
from mcp.types import TextContent
from opentelemetry.propagate import inject
from pydantic import ValidationError

from reliable_agent_lab.mcp_contracts import CapabilityError, ResetFaultResult, ToolErrorCode
from reliable_agent_lab.models import ActionExecution


class ResetOperation(Protocol):
    async def reset_redis_fault(self, action_id: UUID) -> ResetFaultResult: ...

    async def reset_mysql_fault(self, action_id: UUID) -> ResetFaultResult: ...

    async def reset_inventory_latency(self, action_id: UUID) -> ResetFaultResult: ...

    async def reset_payment_5xx(self, action_id: UUID) -> ResetFaultResult: ...


class ActionLedger(Protocol):
    async def begin_action(self, incident_id: UUID, action_id: UUID) -> ActionExecution | None: ...

    async def finish_action(self, result: ActionExecution) -> None: ...


class MCPResetOperation:
    def __init__(self, url: str, timeout_seconds: float) -> None:
        self._url = url
        self._timeout_seconds = timeout_seconds

    async def reset_redis_fault(self, action_id: UUID) -> ResetFaultResult:
        return await self._reset("reset_redis_fault", action_id)

    async def reset_mysql_fault(self, action_id: UUID) -> ResetFaultResult:
        return await self._reset("reset_mysql_fault", action_id)

    async def reset_inventory_latency(self, action_id: UUID) -> ResetFaultResult:
        return await self._reset("reset_inventory_latency", action_id)

    async def reset_payment_5xx(self, action_id: UUID) -> ResetFaultResult:
        return await self._reset("reset_payment_5xx", action_id)

    async def _reset(self, tool_name: str, action_id: UUID) -> ResetFaultResult:
        carrier: dict[str, str] = {}
        inject(carrier)
        arguments = {"action_id": str(action_id), "scope": "local-demo"}
        if traceparent := carrier.get("traceparent"):
            arguments["traceparent"] = traceparent
        try:
            async with asyncio.timeout(self._timeout_seconds):
                async with Client(self._url, read_timeout_seconds=self._timeout_seconds) as client:
                    result = await client.call_tool(
                        tool_name,
                        arguments,
                    )
        except TimeoutError as exc:
            raise CapabilityError(ToolErrorCode.TIMEOUT, "operation MCP timed out") from exc
        except Exception as exc:
            raise CapabilityError(ToolErrorCode.DEPENDENCY, "operation MCP unavailable") from exc
        if result.is_error:
            message = next(
                (block.text for block in result.content if isinstance(block, TextContent)),
                "operation MCP failed",
            )
            code = next(
                (item for item in ToolErrorCode if item.value in message),
                ToolErrorCode.OPERATION,
            )
            raise CapabilityError(code, message[:200])
        if not isinstance(result.structured_content, dict):
            raise CapabilityError(ToolErrorCode.DEPENDENCY, "operation returned no typed payload")
        try:
            return ResetFaultResult.model_validate(result.structured_content)
        except ValidationError as exc:
            raise CapabilityError(ToolErrorCode.DEPENDENCY, "invalid operation payload") from exc
