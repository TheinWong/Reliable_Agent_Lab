"""Wait for a real post-injection inter-service trace in Jaeger."""

import argparse
import time
from datetime import datetime

import httpx
from verify_traces import attribute_value, query_spans, trace_groups


def verify(base_url: str, service: str, started_at: str) -> str:
    start_ns = int(datetime.fromisoformat(started_at).timestamp() * 1_000_000_000)
    expected_name = {
        "inventory-service": "GET /api/inventory/{sku}",
        "payment-service": "GET /api/payments/authorization-preview",
    }[service]
    for attempt in range(30):
        try:
            roots = query_spans(base_url, "order-service", "GET /api/orders/{id}/checkout-preview")
            for root in roots:
                if int(root.get("startTimeUnixNano", "0")) < start_ns:
                    continue
                trace_id = root["traceId"]
                groups = trace_groups(base_url, trace_id)
                children = [
                    span
                    for group in groups
                    if attribute_value(
                        group.get("resource", {}).get("attributes", []), "service.name"
                    )
                    == service
                    for scope in group.get("scopeSpans", [])
                    for span in scope.get("spans", [])
                    if span.get("name") == expected_name
                ]
                if service == "inventory-service" and any(
                    (int(span["endTimeUnixNano"]) - int(span["startTimeUnixNano"])) >= 500_000_000
                    for span in children
                ):
                    return trace_id
                if service == "payment-service" and any(
                    any(
                        attr.get("key") == "http.response.status_code"
                        and int(attr.get("value", {}).get("intValue", "0")) >= 500
                        for attr in span.get("attributes", [])
                    )
                    for span in children
                ):
                    return trace_id
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            pass
        if attempt < 29:
            time.sleep(1)
    raise AssertionError(f"no post-injection {service} failure span linked to order preview")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("service", choices=("inventory-service", "payment-service"))
    parser.add_argument("started_at")
    parser.add_argument("--jaeger-url", default="http://127.0.0.1:16686")
    args = parser.parse_args()
    print(f"downstream trace verified: {verify(args.jaeger_url, args.service, args.started_at)}")
