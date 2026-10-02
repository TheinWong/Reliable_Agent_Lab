from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ToolErrorCode(StrEnum):
    VALIDATION = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    TIMEOUT = "TOOL_TIMEOUT"
    DEPENDENCY = "DEPENDENCY_UNAVAILABLE"
    POLICY = "POLICY_REJECTED"
    OPERATION = "OPERATION_FAILED"


class ToolFailure(BaseModel):
    code: ToolErrorCode
    message: str = Field(max_length=200)
    retryable: bool = False


class DemoLogEvent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    observed_at: datetime = Field(alias="observedAt")
    type: str = Field(max_length=100)
    dependency: str = Field(max_length=100)
    detail: str = Field(max_length=200)


class MetricsSnapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    service: Literal["order-service"]
    redis_unavailable: bool = Field(alias="redisUnavailable")
    cache_read_errors: float = Field(alias="cacheReadErrors", ge=0)
    mysql_cache_error_fallbacks: float = Field(alias="mysqlCacheErrorFallbacks", ge=0)
    mysql_unavailable: bool = Field(default=False, alias="mysqlUnavailable")
    mysql_controlled_failures: float = Field(default=0, alias="mysqlControlledFailures", ge=0)
    inventory_slow_requests: float = Field(default=0, alias="inventorySlowRequests", ge=0)
    payment_preview_errors: float = Field(default=0, alias="paymentPreviewErrors", ge=0)
    inventory_latency_active: bool = Field(default=False, alias="inventoryLatencyActive")
    inventory_fault_started_at: str = Field(default="", alias="inventoryFaultStartedAt")
    payment_http5xx_active: bool = Field(default=False, alias="paymentHttp5xxActive")
    payment_fault_started_at: str = Field(default="", alias="paymentFaultStartedAt")


class LogsSnapshot(BaseModel):
    events: list[DemoLogEvent] = Field(max_length=100)


class TraceSnapshot(BaseModel):
    available: bool
    reason: str = Field(max_length=200)
    spans: list[dict[str, str]] = Field(default_factory=list, max_length=20)


class CacheRecoveryProbe(BaseModel):
    service: Literal["order-service"]
    fault_cleared: bool
    first_source: Literal["DATABASE", "CACHE"]
    second_source: Literal["DATABASE", "CACHE"]


class DownstreamRecoveryProbe(BaseModel):
    service: Literal["order-service"]
    fault_cleared: bool
    preview_status: Literal["OK"]
    inventory_latency_ms: int = Field(ge=0)
    payment_authorized: bool


class ResetFaultResult(BaseModel):
    action_id: UUID
    scope: Literal["local-demo"]
    redis_unavailable: bool = False
    mysql_unavailable: bool = False
    inventory_latency: bool = False
    payment_http5xx: bool = False
    duplicate: bool = False


class CapabilityError(Exception):
    def __init__(self, code: ToolErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
