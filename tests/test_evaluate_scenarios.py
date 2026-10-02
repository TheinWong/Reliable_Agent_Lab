import json
import runpy
from pathlib import Path

evaluate = runpy.run_path("scripts/evaluate_scenarios.py")["evaluate"]


def test_evaluator_rejects_missing_or_unresolved_incident() -> None:
    fixture = json.loads(Path("scenarios/s3-inventory-latency.json").read_text())
    missing = evaluate(fixture, None)
    assert missing["passed"] is False
    incident = {
        "id": "test",
        "run_id": "test-run",
        "status": "completed",
        "diagnosis": fixture["expected_diagnosis_contains"],
        "specialist_reports": [
            {"role": role, "status": "complete", "evidence": []}
            for role in ("metrics", "logs", "trace")
        ],
        "remediation_plan": {
            "action": fixture["expected_action"],
            "target": fixture["expected_target"],
            "scope": "local-demo",
            "risk": "high",
            "action_id": "action",
        },
        "approval": "approved",
        "execution": {"status": "completed", "action_id": "action"},
        "verification": {
            "status": "unresolved",
            "fault_cleared": True,
            "preview_status": "OK",
            "payment_authorized": True,
            "inventory_latency_ms": 25,
        },
        "error_code": None,
    }
    result = evaluate(fixture, incident)
    assert result["passed"] is False
    assert {"verification", "fault_metric", "downstream_trace"} <= set(result["failed_checks"])
