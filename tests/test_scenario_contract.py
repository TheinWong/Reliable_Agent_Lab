import json
from pathlib import Path


def test_s1_and_s2_have_required_ground_truth_fields() -> None:
    required = {
        "id",
        "services",
        "fault_injection",
        "observable_symptoms",
        "expected_evidence",
        "ground_truth_root_cause",
        "allowed_remediation",
        "verification",
        "reset",
        "approval",
    }
    for scenario_id in ("s1-redis-unavailable", "s2-mysql-unavailable"):
        scenario_path = Path(f"scenarios/{scenario_id}.json")
        scenario = json.loads(scenario_path.read_text())
        assert required <= scenario.keys()
        assert scenario["id"] == scenario_id
        assert scenario["reset"]["method"] == "DELETE"
