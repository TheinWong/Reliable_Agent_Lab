from dataclasses import dataclass

from reliable_agent_lab.evidence import LogsCapability, MetricsCapability, TraceCapability
from reliable_agent_lab.models import (
    Evidence,
    ReportStatus,
    SpecialistReport,
    SpecialistRole,
)


@dataclass(frozen=True)
class InvestigationTask:
    incident_id: str
    service: str
    symptom: str


class MetricsAgent:
    role = SpecialistRole.METRICS

    def __init__(self, capability: MetricsCapability) -> None:
        self._capability = capability

    async def investigate(self, task: InvestigationTask) -> SpecialistReport:
        payload = await self._capability.query_metrics(task.service)
        redis_unavailable = payload.get("redisUnavailable") is True
        mysql_unavailable = payload.get("mysqlUnavailable") is True
        inventory_latency = payload.get("inventoryLatencyActive") is True
        payment_http5xx = payload.get("paymentHttp5xxActive") is True
        evidence = Evidence(
            id=f"{task.incident_id}:metrics",
            source_type="metrics",
            source="order-service-metrics",
            payload=payload,
            provenance="mcp://observability-metrics/query_service_metrics",
        )
        return SpecialistReport(
            role=self.role,
            status=ReportStatus.COMPLETE,
            findings=[
                "Redis fault is active" if redis_unavailable else "Redis fault is not active",
                "MySQL fault is active" if mysql_unavailable else "MySQL fault is not active",
                "Inventory latency fault is active"
                if inventory_latency
                else "Inventory latency fault is not active",
                "Payment HTTP 5xx fault is active"
                if payment_http5xx
                else "Payment HTTP 5xx fault is not active",
            ],
            hypotheses=(
                (["Redis cache dependency unavailable"] if redis_unavailable else [])
                + (["MySQL dependency unavailable"] if mysql_unavailable else [])
                + (["Inventory downstream latency"] if inventory_latency else [])
                + (["Payment downstream HTTP 5xx"] if payment_http5xx else [])
            ),
            confidence=0.9
            if any((redis_unavailable, mysql_unavailable, inventory_latency, payment_http5xx))
            else 0.6,
            evidence=[evidence],
            evidence_refs=[evidence.id],
        )


class LogsAgent:
    role = SpecialistRole.LOGS

    def __init__(self, capability: LogsCapability) -> None:
        self._capability = capability

    async def investigate(self, task: InvestigationTask) -> SpecialistReport:
        payload = await self._capability.query_logs(task.service)
        events = payload.get("events", [])
        if not isinstance(events, list):
            raise ValueError("invalid logs capability response")
        recent = events[-100:]

        def failures_after_active_injection(dependency: str, error_type: str) -> int:
            last_injection = -1
            active = False
            for index, event in enumerate(recent):
                if not isinstance(event, dict) or event.get("dependency") != dependency:
                    continue
                if event.get("type") == "demo_fault_injected":
                    last_injection = index
                    active = True
                elif event.get("type") == "demo_fault_reset":
                    active = False
            if not active:
                return 0
            return sum(
                isinstance(event, dict)
                and event.get("dependency") == dependency
                and event.get("type") == error_type
                for event in recent[last_injection + 1 :]
            )

        cache_errors = failures_after_active_injection("redis", "order_cache_read_failed")
        mysql_errors = failures_after_active_injection("mysql", "order_mysql_read_failed")
        inventory_slow = sum(
            isinstance(event, dict) and event.get("type") == "order_inventory_slow"
            for event in recent
        )
        payment_errors = sum(
            isinstance(event, dict) and event.get("type") == "order_payment_request_failed"
            for event in recent
        )
        evidence = Evidence(
            id=f"{task.incident_id}:logs",
            source_type="logs",
            source="order-service-bounded-events",
            payload={"events": recent},
            provenance="mcp://observability-logs/query_recent_logs",
        )
        return SpecialistReport(
            role=self.role,
            status=ReportStatus.COMPLETE,
            findings=[
                f"{cache_errors} recent Redis cache read failures",
                f"{mysql_errors} recent MySQL read failures",
                f"{inventory_slow} recent slow inventory requests",
                f"{payment_errors} recent payment request failures",
            ],
            hypotheses=(
                (["Redis cache dependency unavailable"] if cache_errors else [])
                + (["MySQL dependency unavailable"] if mysql_errors else [])
                + (["Inventory downstream latency"] if inventory_slow else [])
                + (["Payment downstream HTTP 5xx"] if payment_errors else [])
            ),
            confidence=0.85
            if any((cache_errors, mysql_errors, inventory_slow, payment_errors))
            else 0.4,
            evidence=[evidence],
            evidence_refs=[evidence.id],
            missing_information=(
                []
                if any((cache_errors, mysql_errors, inventory_slow, payment_errors))
                else ["no recent active dependency failure event"]
            ),
        )


class TraceAgent:
    role = SpecialistRole.TRACE

    def __init__(self, capability: TraceCapability) -> None:
        self._capability = capability

    async def investigate(self, task: InvestigationTask) -> SpecialistReport:
        payload = await self._capability.query_traces(task.service)
        if payload.get("available") is not True:
            return SpecialistReport(
                role=self.role,
                status=ReportStatus.UNAVAILABLE,
                confidence=0.0,
                missing_information=[str(payload.get("reason", "trace evidence unavailable"))],
            )
        spans = payload.get("spans", [])
        if not isinstance(spans, list):
            raise ValueError("invalid trace capability response")
        evidence = Evidence(
            id=f"{task.incident_id}:trace",
            source_type="trace",
            source="trace-backend",
            payload={"spans": spans[:20]},
            provenance="trace-backend",
        )
        inventory_slow = any(
            isinstance(span, dict)
            and span.get("service") == "inventory-service"
            and span.get("name") == "GET /api/inventory/{sku}"
            and int(span.get("duration_ms", "0")) >= 500
            for span in spans
        )
        payment_http5xx = any(
            isinstance(span, dict)
            and span.get("service") == "payment-service"
            and span.get("name") == "GET /api/payments/authorization-preview"
            and int(span.get("http_status", "0")) >= 500
            for span in spans
        )
        return SpecialistReport(
            role=self.role,
            status=ReportStatus.COMPLETE,
            findings=[f"{len(spans)} recent order-service spans returned"],
            hypotheses=(
                (["Inventory downstream latency"] if inventory_slow else [])
                + (["Payment downstream HTTP 5xx"] if payment_http5xx else [])
            ),
            confidence=0.5 if spans else 0.0,
            evidence=[evidence],
            evidence_refs=[evidence.id],
            missing_information=[] if spans else ["no recent order-service spans"],
        )


def failed_report(role: SpecialistRole, error_code: str) -> SpecialistReport:
    return SpecialistReport(
        role=role,
        status=ReportStatus.FAILED,
        confidence=0.0,
        missing_information=["specialist tool call failed"],
        error_code=error_code,
    )
