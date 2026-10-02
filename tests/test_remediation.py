from uuid import uuid4

from reliable_agent_lab.remediation import RemediationAgent, RiskPolicy


def test_proposal_requires_confirmed_diagnosis_and_has_stable_action_id() -> None:
    agent = RemediationAgent()
    incident_id = uuid4()
    diagnosis = "controlled Redis unavailability detected; MySQL remains authoritative"
    first = agent.propose(incident_id, diagnosis, None)
    second = agent.propose(incident_id, diagnosis, None)
    assert first is not None and second is not None
    assert first.action_id == second.action_id
    assert first.scope == "local-demo"
    assert RiskPolicy().approval_required(first)
    assert agent.propose(incident_id, diagnosis, "INSUFFICIENT_EVIDENCE") is None
    assert agent.propose(incident_id, "no controlled Redis fault detected", None) is None
