# Project Walkthrough

> Codex: maintain this document as implementation advances. It should describe actual code paths, not only intended architecture.

## 1. Repository map
- `src/reliable_agent_lab/api.py`: FastAPI composition and incident HTTP/SSE endpoints.
- `src/reliable_agent_lab/service.py` and `store.py`: incident lifecycle, PostgreSQL-backed resources/events, restart-safe API projection, and graph invocation.
- `src/reliable_agent_lab/graph.py`: parallel specialist fan-out/fan-in, evidence fusion, remediation/policy/approval/execute/verifier nodes.
- `src/reliable_agent_lab/specialists.py`: role-scoped Metrics, Logs, and Trace investigations using typed reports.
- `src/reliable_agent_lab/evidence.py`: separate read-only capability ports and timeout-bounded MCP clients.
- `src/reliable_agent_lab/mcp_server.py` and `mcp_contracts.py`: four independent MCP capability groups and validated payloads.
- `src/reliable_agent_lab/remediation.py` and `operations.py`: typed plan, risk policy, independent verifier, and Operations MCP client.
- `services/order-service`: Java 21 Spring Boot service, MySQL repository, explicit Redis cache-aside logic, fault controls, Actuator and metrics.
- `services/downstream-service`: one Java 21 codebase launched as distinct inventory and payment containers; only the configured role's controller is active.
- `compose.yaml`: MySQL, Redis, PostgreSQL, order/inventory/payment services, Jaeger, four MCP servers, and agent-api stack.
- `scripts/`: smoke and deterministic S1–S4 verification.

## 2. Incident lifecycle
`POST /api/incidents` validates a request, persists a pending resource, publishes `incident.created`, and schedules `IncidentService._run`. The request returns HTTP 202. `_run` projects graph reports, diagnosis, plan, approval pause, execution, and verification back to the PostgreSQL incident resource; events and action outcomes are also persisted. `GET /api/incidents/{id}` reads that resource. SSE replays durable event history, ends at an active approval pause or terminal result, and does not cancel the workflow when disconnected. The task registry remains process-local, while PostgreSQL stores the resumable graph checkpoint and API state.

## 3. Multi-agent delegation
`supervisor_delegate` fans out to separate Metrics, Logs, and Trace graph nodes. Each specialist receives a compact `InvestigationTask` and only its own read-only capability object. Metrics reads current Redis/MySQL fault counters plus inventory/payment fault states and activation times; Logs reads the bounded order event buffer; Trace reads bounded recent Java order-request and checkout-preview spans from Jaeger and distinguishes empty from unavailable. An ID-aware reducer merges reports by role. S1/S2 need current fault metrics and matching logs; S3/S4 additionally need a matching order event and actual downstream span after fault activation. Concurrent faults are marked ambiguous. `tests/test_graph.py::test_specialists_start_in_parallel` uses a barrier to prove concurrent starts. A distinct Remediation Agent proposes a named reset; a separate policy requires approval. The Verifier does not accept the operation result as proof: it probes fault state and fresh order/checkout-preview responses.

## 4. MCP/tools
Metrics, Logs, and Trace specialists each use one role-scoped MCP client over Streamable HTTP. The servers validate typed inputs and outputs. Trace queries Jaeger's v3 API with bounded response size, time range, and result count. The Operations client is wired only to the graph's post-approval execution node; its server exposes four named local-demo resets, guarded by a scope, enable flag, and process-local action/dependency duplicate ledger. The Verifier gets named read-only recovery probes. See `MCP_AND_TOOL_BOUNDARIES.md` for the tool contract table.

## 5. HITL and persistence
`approval_gate` calls LangGraph `interrupt()` before any mutation. The API marks the incident `awaiting_approval`; `POST /api/incidents/{id}/approval` validates the action ID, persists the decision, then resumes the same graph thread with `Command(resume=...)`. PostgreSQL stores graph checkpoints plus API resources/events separately. All four scenario scripts restart agent-api while paused, retrieve the same incident, approve, and observe completion. Duplicate identical approvals return the existing incident. This is a local-demo HITL path, not an authenticated production authorization service.

## 6. Reliability
Evidence calls have MCP and downstream HTTP timeouts and explicit error codes. The graph is acyclic with a recursion limit. Operations retry at most once for timeout/dependency errors using the same deterministic action ID; other errors fail. PostgreSQL records action start/outcome; a completed record stops graph replay from making another MCP call. If a crash falls between the external reset and outcome commit, the Java reset remains safe to retry because it is idempotent. This is not a general exactly-once guarantee. Failed verification currently ends unresolved; semantic replan belongs to a later ExecPlan.

## 7. Observability
The Java service exposes Actuator health and Prometheus metrics. Its demo-only `/internal/evidence/metrics` and `/internal/evidence/logs` endpoints expose bounded, read-only summaries for the first specialist graph. `OrderQueryService` records cache hit/miss/error and MySQL fallback counters and emits structured cache-failure log fields. Fault transitions emit structured logs. The API SSE stream records typed delegation, tool, diagnosis, approval, remediation, and verification events. These events are not spans: `scripts/verify_traces.py` independently queries actual Jaeger data for Agent/tool spans and a Java reset span parented to the Python operation tool span. See `TRACE_WALKTHROUGH.md` for the two-segment restart boundary.

## 8. Scenario walkthrough
Run `make dev-up` then each `make scenario SCENARIO=...` in README order. S1 clears the demo key, activates the fault, proves MySQL fallback with `cacheDegraded=true`, creates an incident, checks three specialist reports and the paused plan, and confirms no reset occurred. S2's controlled uncached MySQL read fault produces a 503; it is not a real network outage or pool exhaustion. S3 calls the real order → inventory → payment checkout-preview path and checks >=500 ms inventory latency. S4 checks a payment-preview 503 and upstream 502 without charging anything. S3/S4 first wait for a real downstream span in the order-preview trace, then create incidents. Every script restarts agent-api at approval, validates a single permitted reset and independent fresh-read recovery, retries approval without a second action, checks Jaeger Java reset parentage, and cleans up its fault on failure.
