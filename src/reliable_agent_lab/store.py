"""API resource/event persistence, separate from LangGraph checkpoints."""

import asyncio
from collections import defaultdict
from typing import Protocol
from uuid import UUID

import psycopg

from reliable_agent_lab.models import (
    ActionExecution,
    IncidentEvent,
    IncidentResponse,
    IncidentStatus,
)


class IncidentStore(Protocol):
    async def setup(self) -> None: ...

    async def create(self, incident: IncidentResponse) -> None: ...

    async def get(self, incident_id: UUID) -> IncidentResponse | None: ...

    async def save(self, incident: IncidentResponse) -> None: ...

    async def append_event(self, event: IncidentEvent) -> IncidentEvent: ...

    async def events_after(self, incident_id: UUID, sequence: int) -> list[IncidentEvent]: ...

    async def incomplete(self) -> list[IncidentResponse]: ...

    async def begin_action(self, incident_id: UUID, action_id: UUID) -> ActionExecution | None: ...

    async def finish_action(self, result: ActionExecution) -> None: ...


class InMemoryIncidentStore:
    def __init__(self) -> None:
        self._incidents: dict[UUID, IncidentResponse] = {}
        self._events: dict[UUID, list[IncidentEvent]] = defaultdict(list)
        self._actions: dict[UUID, ActionExecution] = {}
        self._lock = asyncio.Lock()

    async def setup(self) -> None:
        pass

    async def create(self, incident: IncidentResponse) -> None:
        async with self._lock:
            self._incidents[incident.id] = incident.model_copy(deep=True)

    async def get(self, incident_id: UUID) -> IncidentResponse | None:
        async with self._lock:
            incident = self._incidents.get(incident_id)
            return incident.model_copy(deep=True) if incident else None

    async def save(self, incident: IncidentResponse) -> None:
        async with self._lock:
            self._incidents[incident.id] = incident.model_copy(deep=True)

    async def append_event(self, event: IncidentEvent) -> IncidentEvent:
        async with self._lock:
            event.sequence = len(self._events[event.incident_id]) + 1
            self._events[event.incident_id].append(event.model_copy(deep=True))
            return event.model_copy(deep=True)

    async def events_after(self, incident_id: UUID, sequence: int) -> list[IncidentEvent]:
        async with self._lock:
            return [
                event.model_copy(deep=True)
                for event in self._events[incident_id]
                if event.sequence > sequence
            ]

    async def incomplete(self) -> list[IncidentResponse]:
        async with self._lock:
            return [
                incident.model_copy(deep=True)
                for incident in self._incidents.values()
                if incident.status in {IncidentStatus.PENDING, IncidentStatus.RUNNING}
            ]

    async def begin_action(self, incident_id: UUID, action_id: UUID) -> ActionExecution | None:
        async with self._lock:
            existing = self._actions.get(action_id)
            if existing is None:
                self._actions[action_id] = ActionExecution(action_id=action_id, status="started")
                return None
            if existing.status == "started":
                return None
            return existing.model_copy(deep=True)

    async def finish_action(self, result: ActionExecution) -> None:
        async with self._lock:
            self._actions[result.action_id] = result.model_copy(deep=True)


class PostgresIncidentStore:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    async def setup(self) -> None:
        async with await psycopg.AsyncConnection.connect(self._dsn) as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ral_incidents (
                        id UUID PRIMARY KEY,
                        payload TEXT NOT NULL
                    )
                    """
                )
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ral_action_executions (
                        action_id UUID PRIMARY KEY,
                        incident_id UUID NOT NULL REFERENCES ral_incidents(id),
                        payload TEXT NOT NULL
                    )
                    """
                )
                await cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS ral_incident_events (
                        incident_id UUID NOT NULL REFERENCES ral_incidents(id),
                        sequence INTEGER NOT NULL,
                        payload TEXT NOT NULL,
                        PRIMARY KEY (incident_id, sequence)
                    )
                    """
                )

    async def create(self, incident: IncidentResponse) -> None:
        async with await psycopg.AsyncConnection.connect(self._dsn) as connection:
            await connection.execute(
                "INSERT INTO ral_incidents (id, payload) VALUES (%s, %s)",
                (incident.id, incident.model_dump_json()),
            )

    async def get(self, incident_id: UUID) -> IncidentResponse | None:
        async with await psycopg.AsyncConnection.connect(self._dsn) as connection:
            cursor = await connection.execute(
                "SELECT payload FROM ral_incidents WHERE id = %s", (incident_id,)
            )
            row = await cursor.fetchone()
            return IncidentResponse.model_validate_json(row[0]) if row else None

    async def save(self, incident: IncidentResponse) -> None:
        async with await psycopg.AsyncConnection.connect(self._dsn) as connection:
            await connection.execute(
                "UPDATE ral_incidents SET payload = %s WHERE id = %s",
                (incident.model_dump_json(), incident.id),
            )

    async def append_event(self, event: IncidentEvent) -> IncidentEvent:
        async with await psycopg.AsyncConnection.connect(self._dsn) as connection:
            await connection.execute(
                "SELECT id FROM ral_incidents WHERE id = %s FOR UPDATE", (event.incident_id,)
            )
            cursor = await connection.execute(
                "SELECT COALESCE(MAX(sequence), 0) + 1 "
                "FROM ral_incident_events WHERE incident_id = %s",
                (event.incident_id,),
            )
            row = await cursor.fetchone()
            assert row is not None
            event.sequence = int(row[0])
            await connection.execute(
                "INSERT INTO ral_incident_events (incident_id, sequence, payload) "
                "VALUES (%s, %s, %s)",
                (event.incident_id, event.sequence, event.model_dump_json()),
            )
            return event

    async def events_after(self, incident_id: UUID, sequence: int) -> list[IncidentEvent]:
        async with await psycopg.AsyncConnection.connect(self._dsn) as connection:
            cursor = await connection.execute(
                "SELECT payload FROM ral_incident_events "
                "WHERE incident_id = %s AND sequence > %s ORDER BY sequence",
                (incident_id, sequence),
            )
            return [IncidentEvent.model_validate_json(row[0]) for row in await cursor.fetchall()]

    async def incomplete(self) -> list[IncidentResponse]:
        async with await psycopg.AsyncConnection.connect(self._dsn) as connection:
            cursor = await connection.execute("SELECT payload FROM ral_incidents")
            incidents = [
                IncidentResponse.model_validate_json(row[0]) for row in await cursor.fetchall()
            ]
            return [
                incident
                for incident in incidents
                if incident.status in {IncidentStatus.PENDING, IncidentStatus.RUNNING}
            ]

    async def begin_action(self, incident_id: UUID, action_id: UUID) -> ActionExecution | None:
        started = ActionExecution(action_id=action_id, status="started")
        async with await psycopg.AsyncConnection.connect(self._dsn) as connection:
            await connection.execute(
                "INSERT INTO ral_action_executions (action_id, incident_id, payload) "
                "VALUES (%s, %s, %s) ON CONFLICT (action_id) DO NOTHING",
                (action_id, incident_id, started.model_dump_json()),
            )
            cursor = await connection.execute(
                "SELECT payload FROM ral_action_executions WHERE action_id = %s",
                (action_id,),
            )
            row = await cursor.fetchone()
            assert row is not None
            execution = ActionExecution.model_validate_json(row[0])
            return execution if execution.status != "started" else None

    async def finish_action(self, result: ActionExecution) -> None:
        async with await psycopg.AsyncConnection.connect(self._dsn) as connection:
            await connection.execute(
                "UPDATE ral_action_executions SET payload = %s WHERE action_id = %s",
                (result.model_dump_json(), result.action_id),
            )
