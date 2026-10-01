"""Verify actual S1/S2 OTLP spans through Jaeger's v3 query API."""

import argparse
import time
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx


def attribute_value(attributes: list[dict[str, Any]], key: str) -> str | None:
    for attribute in attributes:
        if attribute.get("key") == key:
            value = attribute.get("value", {})
            return value.get("stringValue")
    return None


def query_spans(base_url: str, service: str, operation: str) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    params: dict[str, str | int] = {
        "query.serviceName": service,
        "query.operationName": operation,
        "query.startTimeMin": (now - timedelta(minutes=10)).isoformat(),
        "query.startTimeMax": now.isoformat(),
        "query.searchDepth": 20,
        "query.pagination.pageSize": 20,
    }
    response = httpx.get(f"{base_url}/api/v3/traces", params=params, timeout=5)
    if response.status_code == 404:
        return []
    response.raise_for_status()
    groups = response.json()["result"]["resourceSpans"]
    return [
        span
        for group in groups
        if attribute_value(group.get("resource", {}).get("attributes", []), "service.name")
        == service
        for scope in group.get("scopeSpans", [])
        for span in scope.get("spans", [])
    ]


def matching_trace(
    spans: list[dict[str, Any]], incident_id: str, root: str
) -> list[dict[str, Any]]:
    roots = [
        span
        for span in spans
        if span.get("name") == root
        and attribute_value(span.get("attributes", []), "ral.incident_id") == incident_id
    ]
    if not roots:
        return []
    trace_id = roots[0]["traceId"]
    return [span for span in spans if span.get("traceId") == trace_id]


def trace_groups(base_url: str, trace_id: str) -> list[dict[str, Any]]:
    response = httpx.get(f"{base_url}/api/v3/traces/{trace_id}", timeout=5)
    response.raise_for_status()
    return response.json()["result"]["resourceSpans"]


def java_reset_spans(base_url: str, trace_id: str, action: str) -> list[dict[str, Any]]:
    service, path = {
        "reset_redis_fault": ("order-service", "/internal/faults/redis-unavailable"),
        "reset_mysql_fault": ("order-service", "/internal/faults/mysql-unavailable"),
        "reset_inventory_latency": ("inventory-service", "/internal/faults/inventory-latency"),
        "reset_payment_5xx": ("payment-service", "/internal/faults/payment-5xx"),
    }[action]
    return [
        span
        for group in trace_groups(base_url, trace_id)
        if attribute_value(group.get("resource", {}).get("attributes", []), "service.name")
        == service
        for scope in group.get("scopeSpans", [])
        for span in scope.get("spans", [])
        if span.get("name") == f"DELETE {path}"
    ]


def verify(
    base_url: str, incident_id: str, run_id: str, action: str = "reset_redis_fault"
) -> tuple[str, str]:
    probe = {
        "reset_redis_fault": "probe_cache_recovery",
        "reset_mysql_fault": "probe_mysql_recovery",
        "reset_inventory_latency": "probe_inventory_recovery",
        "reset_payment_5xx": "probe_payment_recovery",
    }[action]
    for attempt in range(20):
        initial = matching_trace(
            query_spans(base_url, "agent-api", "incident.run"), incident_id, "incident.run"
        )
        resumed = matching_trace(
            query_spans(base_url, "agent-api", "incident.resume"), incident_id, "incident.resume"
        )
        java_operation = (
            "GET /api/orders/{id}/checkout-preview"
            if action in {"reset_inventory_latency", "reset_payment_5xx"}
            else "GET /api/orders/{id}"
        )
        java = query_spans(base_url, "order-service", java_operation)
        java_reset = java_reset_spans(base_url, resumed[0]["traceId"], action) if resumed else []
        if initial and resumed and java and java_reset:
            break
        if attempt < 19:
            time.sleep(1)
    else:
        raise AssertionError("missing exported run/resume, Java order, or Java reset spans")

    initial_names = {span["name"] for span in initial}
    resumed_names = {span["name"] for span in resumed}
    assert {
        "incident.run",
        "agent.supervisor.delegate",
        "agent.metrics",
        "agent.logs",
        "agent.trace",
        "tool.query_service_metrics",
        "tool.query_recent_logs",
        "tool.query_service_traces",
        "agent.supervisor.fuse",
        "agent.remediation",
        "policy.risk",
        "approval.gate",
    } <= initial_names
    assert {
        "incident.resume",
        "approval.gate",
        "operation.execute",
        f"tool.{action}",
        "agent.verifier",
        f"tool.{probe}",
    } <= resumed_names
    for spans, root_name in ((initial, "incident.run"), (resumed, "incident.resume")):
        root = next(span for span in spans if span["name"] == root_name)
        assert attribute_value(root.get("attributes", []), "ral.run_id") == run_id
        assert any(span.get("parentSpanId") == root["spanId"] for span in spans)
    assert initial[0]["traceId"] != resumed[0]["traceId"]
    assert all(len(span.get("traceId", "")) == 32 for span in java)
    reset_tool = next(span for span in resumed if span["name"] == f"tool.{action}")
    assert len(java_reset) == 1
    assert java_reset[0]["parentSpanId"] == reset_tool["spanId"]
    return initial[0]["traceId"], resumed[0]["traceId"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("incident_id")
    parser.add_argument("run_id")
    parser.add_argument(
        "--action",
        choices=(
            "reset_redis_fault",
            "reset_mysql_fault",
            "reset_inventory_latency",
            "reset_payment_5xx",
        ),
        default="reset_redis_fault",
    )
    parser.add_argument("--jaeger-url", default="http://127.0.0.1:16686")
    args = parser.parse_args()
    initial_id, resumed_id = verify(args.jaeger_url, args.incident_id, args.run_id, args.action)
    print(f"trace verification passed: run={initial_id} resume={resumed_id} java=child")
