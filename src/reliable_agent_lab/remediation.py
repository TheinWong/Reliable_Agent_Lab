"""Deterministic S1 remediation proposal and independent server-side policy."""

from typing import Literal, Protocol
from uuid import UUID, uuid5

from reliable_agent_lab.mcp_contracts import CacheRecoveryProbe, DownstreamRecoveryProbe
from reliable_agent_lab.models import RemediationPlan, VerificationResult

_ACTION_NAMESPACE = UUID("2adc5bb4-e2d7-41e0-b3c4-47ea0246a965")


class RemediationAgent:
    def propose(
        self, incident_id: UUID, diagnosis: str, error_code: str | None
    ) -> RemediationPlan | None:
        if error_code is not None:
            return None
        action: Literal[
            "reset_redis_fault", "reset_mysql_fault", "reset_inventory_latency", "reset_payment_5xx"
        ]
        target: Literal["order-service", "inventory-service", "payment-service"] = "order-service"
        if "controlled Redis unavailability detected" in diagnosis:
            action = "reset_redis_fault"
            expected_effect = "restore Redis cache access for order reads"
            rollback = "re-inject the controlled Redis fault in the local demo"
        elif "controlled MySQL unavailability detected" in diagnosis:
            action = "reset_mysql_fault"
            expected_effect = "restore MySQL reads for uncached orders"
            rollback = "re-inject the controlled MySQL fault in the local demo"
        elif "controlled inventory downstream latency detected" in diagnosis:
            action = "reset_inventory_latency"
            target = "inventory-service"
            expected_effect = "restore low-latency inventory checks in checkout preview"
            rollback = "re-inject inventory latency in the local demo"
        elif "controlled payment downstream HTTP 5xx detected" in diagnosis:
            action = "reset_payment_5xx"
            target = "payment-service"
            expected_effect = "restore payment authorization preview responses"
            rollback = "re-inject payment HTTP 5xx in the local demo"
        else:
            return None
        return RemediationPlan(
            action_id=uuid5(_ACTION_NAMESPACE, str(incident_id)),
            action=action,
            target=target,
            scope="local-demo",
            expected_effect=expected_effect,
            rollback=rollback,
        )


class RiskPolicy:
    def approval_required(self, plan: RemediationPlan) -> bool:
        # v0.1 fails closed: every mutating action requires human approval.
        return plan.risk == "high"


class RecoveryCapability(Protocol):
    async def probe_recovery(self, service: str) -> CacheRecoveryProbe: ...

    async def probe_mysql_recovery(self, service: str) -> CacheRecoveryProbe: ...

    async def probe_inventory_recovery(self, service: str) -> DownstreamRecoveryProbe: ...

    async def probe_payment_recovery(self, service: str) -> DownstreamRecoveryProbe: ...


class VerifierAgent:
    def __init__(self, recovery: RecoveryCapability) -> None:
        self._recovery = recovery

    async def verify(self, service: str, action: str = "reset_redis_fault") -> VerificationResult:
        if action == "reset_inventory_latency":
            downstream = await self._recovery.probe_inventory_recovery(service)
            resolved = (
                downstream.fault_cleared
                and downstream.preview_status == "OK"
                and downstream.inventory_latency_ms < 500
                and downstream.payment_authorized
            )
            return VerificationResult(
                status="resolved" if resolved else "unresolved",
                fault_cleared=downstream.fault_cleared,
                preview_status=downstream.preview_status,
                inventory_latency_ms=downstream.inventory_latency_ms,
                payment_authorized=downstream.payment_authorized,
                explanation=(
                    "fresh checkout preview completed with normal inventory latency"
                    if resolved
                    else "fresh checkout preview did not establish normal inventory latency"
                ),
            )
        if action == "reset_payment_5xx":
            downstream = await self._recovery.probe_payment_recovery(service)
            resolved = (
                downstream.fault_cleared
                and downstream.preview_status == "OK"
                and downstream.payment_authorized
            )
            return VerificationResult(
                status="resolved" if resolved else "unresolved",
                fault_cleared=downstream.fault_cleared,
                preview_status=downstream.preview_status,
                inventory_latency_ms=downstream.inventory_latency_ms,
                payment_authorized=downstream.payment_authorized,
                explanation=(
                    "fresh checkout preview received a successful payment response"
                    if resolved
                    else "fresh checkout preview did not establish payment recovery"
                ),
            )
        if action == "reset_redis_fault":
            probe = await self._recovery.probe_recovery(service)
            explanation = "fault cleared, MySQL read repopulated Redis, then cache hit"
        elif action == "reset_mysql_fault":
            probe = await self._recovery.probe_mysql_recovery(service)
            explanation = "MySQL fault cleared, database read succeeded, then cache hit"
        else:
            raise ValueError("unsupported verification action")
        resolved = (
            probe.fault_cleared
            and probe.first_source == "DATABASE"
            and probe.second_source == "CACHE"
        )
        return VerificationResult(
            status="resolved" if resolved else "unresolved",
            fault_cleared=probe.fault_cleared,
            first_source=probe.first_source,
            second_source=probe.second_source,
            explanation=(
                explanation
                if resolved
                else "fresh reads did not establish database repopulation and cache hit"
            ),
        )
