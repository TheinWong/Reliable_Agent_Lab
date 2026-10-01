# System Architecture

## Runtime components

### Agent API
FastAPI service that accepts incidents, exposes status/events, handles approvals and owns application-level orchestration entrypoints.

### LangGraph Runtime
Runs the multi-agent workflow and persists state/checkpoints.

### Agent roles
- Supervisor: delegation, evidence fusion, root-cause decision and safe termination; semantic replan is not implemented in v0.1.
- Metrics Agent: metrics and health evidence.
- Logs Agent: log/error-pattern evidence.
- Trace Agent: distributed-trace/topology evidence.
- Remediation Agent: proposes typed recovery plan; does not directly self-approve risky actions.
- Verifier Agent: independently re-collects evidence after actions.

### MCP servers
Implemented capability boundaries:
- observability-metrics;
- observability-logs;
- observability-traces;
- operations.
The Verifier uses named read-only probes on the Metrics server. No unrestricted database MCP server is exposed.

### Demo environment
Implemented:
- order-service;
- inventory-service;
- payment-service;
- MySQL;
- Redis.
Services remain intentionally small.

### Observability
- Spring Boot Actuator / Micrometer;
- Prometheus-format Actuator endpoints (no standalone Prometheus server in v0.1);
- OpenTelemetry instrumentation;
- Jaeger for trace inspection;
- structured application/agent logs.

## End-to-end flow
1. Scenario injects a named local fault and creates an incident. General monitoring/alert ingestion is not implemented.
2. API starts an incident workflow.
3. Supervisor fans out to the three fixed investigation roles.
4. Specialists query their read-only MCP tools in parallel.
5. Supervisor merges typed reports and decides whether evidence is sufficient.
6. Remediation Agent produces a typed plan.
7. Policy layer requires approval for every local mutating reset.
8. Operations tool executes an idempotent action.
9. Verifier independently collects post-action evidence.
10. Workflow ends as resolved or fails explicitly; semantic replan is deferred.

S1–S4 reach step 9 through an approval interrupt and independent recovery probe. Jaeger records Agent/tool and Java service spans; the approved reset carries W3C trace context across the MCP/Java boundary. The Trace specialist reads bounded recent order-read and checkout-preview evidence, including real inventory/payment spans. A failed verification ends explicitly.

```text
FastAPI incident API ── PostgreSQL resources/events + LangGraph checkpoints
         │
         ▼
Supervisor ── fan-out ── Metrics MCP → order/inventory/payment fault state
         │             ├─ Logs MCP    → bounded order events
         │             └─ Trace MCP   → Jaeger v3 query
         ▼
Remediation plan → policy → approval interrupt → Operations MCP → named reset
         │                                                │
         └────────────── independent Verifier ← read-only probe

order-service → MySQL (source of truth) + Redis (cache)
              → inventory-service → payment-service (stateless preview)
Java and Python spans → Jaeger (ephemeral storage)
```

## Deployment boundary
The deterministic v0.1 demo runs locally with Docker Compose and requires no remote LLM inference. It is not an authenticated production SRE service.
