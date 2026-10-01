from datetime import UTC, datetime
from uuid import uuid4

from reliable_agent_lab.models import (
    ActionExecution,
    IncidentEvent,
    IncidentResponse,
    IncidentStatus,
    Severity,
)
from reliable_agent_lab.store import InMemoryIncidentStore


async def test_store_copies_resources_and_sequences_events() -> None:
    store = InMemoryIncidentStore()
    await store.setup()
    incident = IncidentResponse(
        id=uuid4(),
        run_id=uuid4(),
        service="order-service",
        symptom="cache failure",
        severity=Severity.MEDIUM,
        scenario_id=None,
        status=IncidentStatus.PENDING,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await store.create(incident)
    incident.status = IncidentStatus.RUNNING
    assert (await store.get(incident.id)).status == IncidentStatus.PENDING
    await store.save(incident)
    assert (await store.get(incident.id)).status == IncidentStatus.RUNNING

    event = IncidentEvent(
        sequence=0,
        incident_id=incident.id,
        run_id=incident.run_id,
        type="incident.created",
    )
    first = await store.append_event(event)
    second = await store.append_event(event.model_copy(update={"type": "incident.running"}))
    assert [first.sequence, second.sequence] == [1, 2]
    assert [item.type for item in await store.events_after(incident.id, 1)] == ["incident.running"]
    action_id = uuid4()
    assert await store.begin_action(incident.id, action_id) is None
    await store.finish_action(ActionExecution(action_id=action_id, status="completed"))
    repeated = await store.begin_action(incident.id, action_id)
    assert repeated is not None
    assert repeated.status == "completed"
