"""Exercise the actual Compose MCP transport and scoped reset idempotency."""

import asyncio
import os
from uuid import uuid4

import httpx
from mcp import Client


async def verify_tool_set(url: str, expected: set[str], read_only: bool) -> None:
    async with Client(url, read_timeout_seconds=5) as client:
        tools = (await client.list_tools()).tools
        assert {tool.name for tool in tools} == expected
        assert all(tool.annotations is not None for tool in tools)
        assert all(
            tool.annotations.read_only_hint is read_only for tool in tools if tool.annotations
        )


async def run() -> None:
    metrics_url = os.getenv("RAL_METRICS_MCP_URL", "http://mcp-metrics:8000/mcp")
    logs_url = os.getenv("RAL_LOGS_MCP_URL", "http://mcp-logs:8000/mcp")
    traces_url = os.getenv("RAL_TRACES_MCP_URL", "http://mcp-traces:8000/mcp")
    operations_url = "http://mcp-operations:8000/mcp"
    order_url = os.getenv("RAL_ORDER_SERVICE_URL", "http://order-service:8080")

    async with asyncio.timeout(30):
        await verify_tool_set(
            metrics_url,
            {
                "query_service_metrics",
                "probe_cache_recovery",
                "probe_mysql_recovery",
                "probe_inventory_recovery",
                "probe_payment_recovery",
            },
            True,
        )
        await verify_tool_set(logs_url, {"query_recent_logs"}, True)
        await verify_tool_set(traces_url, {"query_service_traces"}, True)
        await verify_tool_set(
            operations_url,
            {
                "reset_redis_fault",
                "reset_mysql_fault",
                "reset_inventory_latency",
                "reset_payment_5xx",
            },
            False,
        )

        async with httpx.AsyncClient(timeout=5) as http:
            try:
                inject = await http.put(f"{order_url}/internal/faults/redis-unavailable")
                inject.raise_for_status()
                assert inject.json()["redisUnavailable"] is True

                action_id = str(uuid4())
                async with Client(operations_url, read_timeout_seconds=5) as client:
                    first = await client.call_tool(
                        "reset_redis_fault", {"action_id": action_id, "scope": "local-demo"}
                    )
                    second = await client.call_tool(
                        "reset_redis_fault", {"action_id": action_id, "scope": "local-demo"}
                    )
                assert not first.is_error and not second.is_error
                assert first.structured_content["duplicate"] is False
                assert second.structured_content["duplicate"] is True
                assert first.structured_content["redis_unavailable"] is False
                status = await http.get(f"{order_url}/internal/faults")
                status.raise_for_status()
                assert status.json()["redisUnavailable"] is False
            finally:
                reset = await http.delete(f"{order_url}/internal/faults/redis-unavailable")
                reset.raise_for_status()

    print("MCP smoke passed: four scoped tool groups and duplicate-safe reset")


if __name__ == "__main__":
    asyncio.run(run())
