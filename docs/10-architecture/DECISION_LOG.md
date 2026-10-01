# Architecture Decision Log

Use this file as an index. Significant decisions should be recorded as short ADR sections or separate ADR files if the list grows.

## ADR-001 — LangGraph as primary orchestrator
Status: accepted.
Reason: explicit state/graph/handoff representation, suitable for stateful multi-step agent workflows, checkpoints and controlled routing. Avoid mixing multiple orchestration frameworks in v0.1.

## ADR-002 — Multi-agent split by responsibility and permission
Status: accepted.
Reason: specialists have materially different evidence sources and can investigate in parallel; remediation and verification need independence; read-only and mutating capabilities should be isolated.

## ADR-003 — MCP for external capability boundary
Status: accepted.
Reason: standard typed tool integration and replaceable external implementations; agent graph should not depend directly on every telemetry backend.

## ADR-004 — Microservice incidents as validation environment, not product identity
Status: accepted.
Reason: provides realistic tool calls, failures and measurable success while keeping the repository relevant to Agent Engineering roles.

## ADR-005 — MySQL-authoritative cache-aside semantics
Status: accepted.
Context: S1 needs Redis failure to remain observable without turning a cache dependency into the order system of record.
Decision: MySQL is authoritative. A Redis hit may serve the order; a miss reads MySQL and best-effort populates Redis. A Redis read error is recorded separately from a miss, falls back to MySQL, and skips cache population for that request. Cache write failure does not invalidate a successful database read.
Alternatives considered: fail all reads when Redis is unavailable; hide errors as cache misses; use annotation-driven caching.
Consequences: order reads remain available during the controlled cache fault while logs, metrics, and the response retain degraded evidence. The explicit code path is longer but testable.
Evidence/tests: `OrderQueryServiceTest`, `scripts/smoke.sh`, and `scripts/scenarios/redis-unavailable.sh`.

## ADR-006 — Deterministic first-slice control plane
Status: accepted for ExecPlan 0001; planned replacement is documented.
Context: core graph/API behavior and a real Java dependency must be testable without model credentials or full MCP/durable infrastructure.
Decision: the first slice uses deterministic LangGraph nodes, an in-process incident store/task registry, and typed HTTP evidence adapters. External calls have explicit timeouts. The graph does not claim remediation, verification, or durable resume.
Alternatives considered: block on a live LLM; create fake MCP and persistence layers before a real service existed.
Consequences: CI is deterministic and the vertical slice is real, but process restart loses incident state. Later ExecPlans replace adapters with MCP and memory state with durable checkpoints without unnecessarily changing the public incident resource shape.
Evidence/tests: Python tests, `scripts/smoke.sh`, and README limitations.

## ADR-007 — Parallel role-scoped investigation before MCP transport
Status: accepted for ExecPlan 0002.
Context: the first graph collected evidence through one broad adapter, so it could not demonstrate specialist isolation or concurrent delegation.
Decision: LangGraph Supervisor fans out to independent Metrics, Logs, and Trace nodes. Each role receives a compact immutable task and only its own read-only capability port. Reports are Pydantic-validated and merged by role identity, replacing retries rather than duplicating them. S1 fusion requires current fault metrics and cache-failure logs after the latest injection. Trace reports unavailable until a real backend is wired.
Alternatives considered: one node calling all tools; sequentially named specialists; fabricated trace spans.
Consequences: graph mechanics and permission shape are testable without model credentials, but HTTP adapters remain temporary and tracing is incomplete.
Evidence/tests: barrier concurrency test, reducer and failure tests, S1 scenario report/SSE assertions.

## ADR-008 — Scoped MCP servers before automatic operations
Status: accepted for ExecPlan 0003.
Context: role-scoped HTTP adapters isolated specialist interfaces but did not provide a standard external tool transport; exposing mutations during investigation would also bypass future risk/approval gates.
Decision: run four separate MCP servers for metrics, logs, traces, and operations. Inject only the three read-only URLs into the graph. Validate Pydantic payloads at server and client boundaries, bound calls by timeouts, and surface typed tool failures. The operations server exposes only a local-demo Redis-fault reset with enable flag, scope, UUID duplicate guard, and no graph caller. Trace returns unavailable until real spans exist.
Alternatives considered: one broad server/URL for every role; pretending SSE events are distributed traces; automatic operations before HITL.
Consequences at ExecPlan 0003: S1 investigation traversed real MCP transport and capability isolation became testable; operations graph use was added in ADR-009. Durable operation idempotency and real trace evidence remain open.
Evidence/tests: `tests/test_mcp_contracts.py`, `make mcp-smoke`, `make scenario SCENARIO=redis-unavailable`.

## ADR-009 — Persist graph and API state separately for S1 approval
Status: accepted for ExecPlan 0004.
Context: a LangGraph checkpoint alone cannot restore an API incident resource or its SSE event history after agent-api restart. Mutating remediation must not run before a human decision, and a tool success cannot establish service recovery.
Decision: use PostgreSQL `AsyncPostgresSaver` for graph checkpoints and a small PostgreSQL incident/event store for API projection. A deterministic Remediation Agent proposes only the named Redis reset; a server-side policy requires approval. LangGraph interrupts before execution; the approval endpoint persists the decision and resumes the same thread. A separate Verifier reads fresh fault/order evidence through MCP. The stable action ID and idempotent Java reset constrain retries.
Alternatives considered: in-memory approval flags; a synchronous confirmation prompt; treating reset response or container health as verification.
Consequences: S1 survives a restart while waiting for approval and demonstrates independent recovery evidence. PostgreSQL records action start/outcome to prevent a completed call from replaying, while Java reset makes an ambiguous post-call crash safe to retry. The demo approval API has no production authentication; semantic replan and general exactly-once external effects remain open.
Evidence/tests: `tests/test_workflow.py`, `tests/test_api.py`, and `scripts/scenarios/redis-unavailable.sh` with agent-api restart.

## ADR-010 — Explicit S1 OTLP spans and bounded Jaeger evidence
Status: accepted for ExecPlan 0005.
Context: SSE and structured logs expose workflow events but cannot prove trace parentage or Java operation continuity. Jaeger must be a real evidence source, not a source of synthetic specialist spans.
Decision: run pinned Jaeger 2.21 in Compose with in-memory storage; emit explicit Python SDK spans around incident, graph-node, and tool boundaries; attach the pinned OpenTelemetry Java agent 2.31.1 to order-service. Trace MCP queries only recent order-request traces through Jaeger's v3 API with time/result/byte caps. The approved reset forwards a validated W3C `traceparent` as a typed Operations MCP argument to the Java HTTP call. The approval restart starts a new trace segment linked by incident/run attributes.
Alternatives considered: count SSE events as traces; return fabricated Trace specialist data; assume implicit context propagation through all MCP transport layers.
Consequences: S1 has actual Python and Java spans and a cross-service reset parent link. Jaeger data is ephemeral, read-only tool calls are not all one distributed trace, and production telemetry/authentication remain out of scope.
Evidence/tests: `tests/test_mcp_contracts.py`, `tests/test_workflow.py`, `scripts/verify_traces.py`, and `make scenario SCENARIO=redis-unavailable`.

## ADR-011 — Scenario-specific controlled MySQL read fault
Status: accepted for S2 in ExecPlan 0006.
Context: S1's cache failure does not exercise an authoritative-store read failure, while arbitrary SQL or Docker control would violate the bounded operations boundary.
Decision: inject a local-only MySQL read fault at the order-service application boundary for uncached reads. Emit an explicit 503, counter and structured event. Metrics and Logs specialists require an active matching fault and post-injection failure before the Supervisor diagnoses S2. A distinct approval-gated `reset_mysql_fault` MCP tool and independent `probe_mysql_recovery` check a fresh database read followed by a cache hit. The scenario restarts agent-api while paused and asserts idempotency and Java trace parentage.
Alternatives considered: stop MySQL through an unrestricted agent tool; claim a simulated failure is a real network outage.
Consequences: deterministic S2 is safe and reproducible, but it does not validate physical connection failure, Hikari pool exhaustion, or full database outage recovery. Those distinctions remain explicit in the scenario fixture and README.
Evidence/tests: `tests/test_graph.py`, `tests/test_workflow.py`, `tests/test_mcp_contracts.py`, `make scenario SCENARIO=mysql-unavailable`.

## ADR-012 — Bounded downstream faults with post-injection three-source evidence
Status: accepted for S3/S4 in ExecPlan 0006.
Context: an order-only demo cannot prove multi-service latency/error topology, while historical logs or spans could make a newly active fault appear confirmed without a fresh failed request.
Decision: run separate inventory and payment Spring Boot containers, called by a real order checkout-preview path. Inventory injects a fixed 800 ms delay; payment's stateless authorization preview injects HTTP 503 without making a charge. The Metrics MCP tool reads each current fault state and activation timestamp; Supervisor requires matching bounded order event and Jaeger downstream span after that timestamp. Named local-demo resets remain approval-gated, and distinct read-only probes perform fresh checkout-preview requests after reset.
Alternatives considered: fabricated trace spans; unbounded service restart/shell tools; diagnosis from current fault state alone.
Consequences: S3/S4 are reproducible and show real HTTP propagation, but exercise controlled faults rather than arbitrary production failures. The bounded Jaeger query can yield insufficient evidence if trace export is delayed; scenarios wait for export before incident creation.
Evidence/tests: `tests/test_graph.py`, `tests/test_mcp_contracts.py`, `scripts/verify_downstream_trace.py`, `make scenario SCENARIO=inventory-latency`, `make scenario SCENARIO=payment-5xx`.

## Template for future decisions
### ADR-NNN — Title
Status: proposed / accepted / superseded
Context:
Decision:
Alternatives considered:
Consequences:
Evidence/tests:
