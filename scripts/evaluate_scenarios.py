"""Evaluate the latest persisted S1-S4 incidents against machine-readable fixtures.

This checks persisted control-plane outcomes; scenario scripts separately prove live
HTTP symptoms and Jaeger parentage. It is not a statistical benchmark.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def latest_incidents() -> dict[str, dict[str, Any]]:
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "agentlab",
        "-d",
        "agentlab",
        "-t",
        "-A",
        "-c",
        "SELECT payload FROM ral_incidents WHERE payload::jsonb ->> 'scenario_id' "
        "IN ('s1-redis-unavailable','s2-mysql-unavailable',"
        "'s3-inventory-latency','s4-payment-5xx')",
    ]
    completed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True)
    latest: dict[str, dict[str, Any]] = {}
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        incident = json.loads(line)
        scenario_id = incident["scenario_id"]
        if scenario_id not in latest or incident["created_at"] > latest[scenario_id]["created_at"]:
            latest[scenario_id] = incident
    return latest


def evaluate(fixture: dict[str, Any], incident: dict[str, Any] | None) -> dict[str, Any]:
    if incident is None:
        return {
            "scenario_id": fixture["id"],
            "passed": False,
            "failed_checks": ["incident missing"],
        }
    reports = {report["role"]: report for report in incident["specialist_reports"]}
    plan = incident.get("remediation_plan") or {}
    execution = incident.get("execution") or {}
    verification = incident.get("verification") or {}
    checks = {
        "completed": incident["status"] == "completed",
        "root_cause": fixture["expected_diagnosis_contains"] in (incident["diagnosis"] or ""),
        "specialists": set(reports) == {"metrics", "logs", "trace"}
        and all(report["status"] == "complete" for report in reports.values()),
        "remediation": plan.get("action") == fixture["expected_action"]
        and plan.get("target") == fixture["expected_target"]
        and plan.get("scope") == "local-demo",
        "approval": incident.get("approval") == "approved" and plan.get("risk") == "high",
        "execution": execution.get("status") == "completed"
        and execution.get("action_id") == plan.get("action_id"),
        "verification": verification.get("status") == "resolved"
        and verification.get("fault_cleared") is True,
        "no_error": incident.get("error_code") is None,
    }
    if fixture["id"] in {"s1-redis-unavailable", "s2-mysql-unavailable"}:
        checks["fresh_order_recovery"] = (
            verification.get("first_source") == "DATABASE"
            and verification.get("second_source") == "CACHE"
        )
    else:
        checks["fresh_preview_recovery"] = (
            verification.get("preview_status") == "OK"
            and verification.get("payment_authorized") is True
            and isinstance(verification.get("inventory_latency_ms"), int)
            and verification["inventory_latency_ms"] < 500
        )
        metric_evidence = reports.get("metrics", {}).get("evidence", [])
        trace_evidence = reports.get("trace", {}).get("evidence", [])
        fault_field = (
            "inventoryLatencyActive"
            if fixture["id"] == "s3-inventory-latency"
            else "paymentHttp5xxActive"
        )
        downstream = fixture["expected_target"]
        checks["fault_metric"] = any(
            item.get("payload", {}).get(fault_field) is True for item in metric_evidence
        )
        checks["downstream_trace"] = any(
            span.get("service") == downstream
            and (
                int(span.get("duration_ms", "0")) >= 500
                if downstream == "inventory-service"
                else int(span.get("http_status", "0") or "0") >= 500
            )
            for item in trace_evidence
            for span in item.get("payload", {}).get("spans", [])
        )
    failed = [name for name, passed in checks.items() if not passed]
    return {
        "scenario_id": fixture["id"],
        "incident_id": incident["id"],
        "run_id": incident["run_id"],
        "passed": not failed,
        "failed_checks": failed,
    }


def main() -> None:
    latest = latest_incidents()
    results = [
        evaluate(json.loads(path.read_text()), latest.get(path.stem))
        for path in sorted((ROOT / "scenarios").glob("s[1-4]-*.json"))
    ]
    report = {
        "scope": "latest persisted local incident per S1-S4 fixture",
        "passed": sum(result["passed"] for result in results),
        "total": len(results),
        "results": results,
    }
    print(json.dumps(report, indent=2))
    if report["passed"] != 4 or report["total"] != 4:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
