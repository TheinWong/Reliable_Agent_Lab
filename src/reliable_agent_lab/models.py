from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IncidentStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class ApprovalDecision(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRequest(BaseModel):
    action_id: UUID
    approved: bool


class RemediationPlan(BaseModel):
    action_id: UUID
    action: Literal[
        "reset_redis_fault",
        "reset_mysql_fault",
        "reset_inventory_latency",
        "reset_payment_5xx",
    ]
    target: Literal["order-service", "inventory-service", "payment-service"]
    scope: Literal["local-demo"]
    risk: Literal["high"] = "high"
    expected_effect: str = Field(max_length=200)
    rollback: str = Field(max_length=200)


class ActionExecution(BaseModel):
    action_id: UUID
    status: Literal["started", "completed", "failed"]
    duplicate: bool = False
    error_code: str | None = None


class VerificationResult(BaseModel):
    status: Literal["resolved", "unresolved"]
    fault_cleared: bool
    first_source: str = ""
    second_source: str = ""
    preview_status: str | None = None
    inventory_latency_ms: int | None = None
    payment_authorized: bool | None = None
    explanation: str = Field(max_length=300)


class IncidentCreateRequest(BaseModel):
    service: str = Field(default="order-service", min_length=1, max_length=100)
    symptom: str = Field(min_length=1, max_length=500)
    severity: Severity = Severity.MEDIUM
    scenario_id: str | None = Field(default=None, max_length=100)


class Evidence(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    source_type: str
    source: str
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any]
    provenance: str


class SpecialistRole(StrEnum):
    METRICS = "metrics"
    LOGS = "logs"
    TRACE = "trace"


class ReportStatus(StrEnum):
    COMPLETE = "complete"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class SpecialistReport(BaseModel):
    role: SpecialistRole
    status: ReportStatus
    findings: list[str] = Field(default_factory=list, max_length=10)
    hypotheses: list[str] = Field(default_factory=list, max_length=5)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list, max_length=10)
    evidence_refs: list[str] = Field(default_factory=list, max_length=10)
    missing_information: list[str] = Field(default_factory=list, max_length=5)
    error_code: str | None = None


class IncidentResponse(BaseModel):
    id: UUID
    run_id: UUID
    service: str
    symptom: str
    severity: Severity
    scenario_id: str | None
    status: IncidentStatus
    diagnosis: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    specialist_reports: list[SpecialistReport] = Field(default_factory=list)
    remediation_plan: RemediationPlan | None = None
    approval: ApprovalDecision | None = None
    execution: ActionExecution | None = None
    verification: VerificationResult | None = None
    error_code: str | None = None
    created_at: datetime
    updated_at: datetime


class IncidentEvent(BaseModel):
    sequence: int
    incident_id: UUID
    run_id: UUID
    type: str
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data: dict[str, Any] = Field(default_factory=dict)
