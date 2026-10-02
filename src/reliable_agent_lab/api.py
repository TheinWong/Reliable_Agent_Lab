import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from reliable_agent_lab.config import Settings
from reliable_agent_lab.evidence import (
    InvestigationCapabilities,
    MCPRecoveryClient,
    mcp_investigation_capabilities,
)
from reliable_agent_lab.models import ApprovalRequest, IncidentCreateRequest, IncidentResponse
from reliable_agent_lab.operations import MCPResetOperation, ResetOperation
from reliable_agent_lab.remediation import RecoveryCapability
from reliable_agent_lab.service import ApprovalConflictError, IncidentNotFoundError, IncidentService
from reliable_agent_lab.store import PostgresIncidentStore
from reliable_agent_lab.telemetry import configure_tracing


def create_app(
    capabilities: InvestigationCapabilities | None = None,
    operations: ResetOperation | None = None,
    recovery: RecoveryCapability | None = None,
) -> FastAPI:
    settings = Settings()
    resolved_capabilities = capabilities or mcp_investigation_capabilities(
        str(settings.metrics_mcp_url),
        str(settings.logs_mcp_url),
        str(settings.traces_mcp_url),
        settings.tool_timeout_seconds,
    )
    resolved_operations = operations
    resolved_recovery = recovery
    if settings.postgres_dsn and operations is None and recovery is None:
        resolved_operations = MCPResetOperation(
            str(settings.operations_mcp_url), settings.tool_timeout_seconds
        )
        resolved_recovery = MCPRecoveryClient(
            str(settings.metrics_mcp_url), settings.tool_timeout_seconds
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        provider = configure_tracing("agent-api", os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"))
        try:
            if settings.postgres_dsn:
                async with AsyncPostgresSaver.from_conn_string(
                    settings.postgres_dsn
                ) as checkpointer:
                    await checkpointer.setup()
                    service = IncidentService(
                        resolved_capabilities,
                        PostgresIncidentStore(settings.postgres_dsn),
                        checkpointer,
                        resolved_operations,
                        resolved_recovery,
                    )
                    await service.setup()
                    app.state.incident_service = service
                    yield
            else:
                memory_checkpointer = InMemorySaver() if resolved_operations is not None else None
                service = IncidentService(
                    resolved_capabilities,
                    checkpointer=memory_checkpointer,
                    operations=resolved_operations,
                    recovery=resolved_recovery,
                )
                await service.setup()
                app.state.incident_service = service
                yield
        finally:
            if provider is not None:
                provider.shutdown()

    app = FastAPI(title="Reliable Agent Lab", version="0.1.0-dev", lifespan=lifespan)

    def service() -> IncidentService:
        return cast(IncidentService, app.state.incident_service)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "UP"}

    @app.post(
        "/api/incidents",
        response_model=IncidentResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def create_incident(request: IncidentCreateRequest) -> IncidentResponse:
        return await service().create(request)

    @app.get("/api/incidents/{incident_id}", response_model=IncidentResponse)
    async def get_incident(incident_id: UUID) -> IncidentResponse:
        try:
            return await service().get(incident_id)
        except IncidentNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "INCIDENT_NOT_FOUND", "message": str(exc)},
            ) from exc

    @app.post(
        "/api/incidents/{incident_id}/approval",
        response_model=IncidentResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def decide_approval(incident_id: UUID, request: ApprovalRequest) -> IncidentResponse:
        try:
            return await service().approve(incident_id, request)
        except IncidentNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "INCIDENT_NOT_FOUND", "message": str(exc)},
            ) from exc
        except ApprovalConflictError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "APPROVAL_CONFLICT", "message": str(exc)},
            ) from exc

    @app.get("/api/incidents/{incident_id}/events")
    async def stream_events(incident_id: UUID) -> StreamingResponse:
        try:
            await service().get(incident_id)
        except IncidentNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "INCIDENT_NOT_FOUND", "message": str(exc)},
            ) from exc

        async def generate() -> AsyncIterator[str]:
            async for event in service().events(incident_id):
                payload: dict[str, Any] = event.model_dump(mode="json")
                yield f"event: {event.type}\ndata: {json.dumps(payload)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    return app


app = create_app()
