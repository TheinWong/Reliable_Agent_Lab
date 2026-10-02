# ExecPlan 0005 — OpenTelemetry and Real Trace Evidence

## Objective
Make the S1 runtime observable in Jaeger with actual Supervisor, specialist, MCP tool, approval/resume, operation, Verifier, and Java order-service spans. Replace the Trace specialist's placeholder unavailable response with bounded evidence from a real Jaeger backend, while preserving explicit unavailable behavior when the backend is down.

## Relevant repository context
`AGENTS.md`, `CODEX_GOAL.md`, `.agent/PLANS.md`; `docs/20-engineering/OBSERVABILITY.md`, `docs/10-architecture/{SYSTEM_ARCHITECTURE,MCP_AND_TOOL_BOUNDARIES}.md`, `docs/90-learning/TRACE_WALKTHROUGH.md`; Python graph/service/evidence/MCP modules, Java order-service Dockerfile/pom, Compose, S1 script, CI.

## Acceptance criteria
- A pinned Jaeger instance boots in Compose and accepts OTLP traces; its query API or UI can retrieve a trace produced by the actual S1 scenario.
- Python emits OpenTelemetry spans for incident run, Supervisor delegation/fusion, parallel specialists, MCP tool calls, approval/resume, remediation execution, and independent verification, correlated by incident/run/action identity with bounded safe attributes.
- Java order-service emits real HTTP/cache-path spans; trace context is propagated where practical so at least one scenario trace crosses service/tool boundaries, or any split is explicitly documented and linked by correlation ID.
- Trace MCP queries Jaeger for bounded, recent, real order-service span evidence and returns typed provenance; it reports unavailable/empty distinctly and never fabricates spans.
- Automated checks assert actual exported spans and parent/child or correlation relationships, not merely SSE events or instrumentation configuration.
- Python/Java gates, clean Compose boot, smoke, S1, and trace-specific verification pass; README, roadmap, ADR, and trace walkthrough match observed data.

## Non-goals
Persistent Jaeger storage, full production telemetry pipeline, metrics dashboards, or S2–S4 scenario implementation. Do not use synthetic spans as evidence for the Trace specialist.

## Design / approach
Use the OpenTelemetry Python SDK with OTLP/HTTP exporter and explicit spans around existing graph/tool boundaries; keep no-op tracing for local unit tests without an exporter. Run Jaeger v2 all-in-one with in-memory trace storage for the demo. Use OpenTelemetry Java agent or supported Spring Boot instrumentation for the Java service, with pinned version and OTLP settings. Prefer Jaeger's documented v3 query API for Trace MCP and verification; cap time range, trace/span counts, and payload sizes. Treat approval restart as a new process segment linked by `run_id` if one continuous context cannot safely survive the pause.

## Work breakdown
- [x] pin SDK/Jaeger/Java instrumentation versions and confirm query contract
- [x] add Jaeger and OTLP export configuration to Compose
- [x] add Python incident/agent/tool spans and safe correlation attributes
- [x] instrument Java order-service and propagate context for the approved reset
- [x] replace Trace MCP placeholder with bounded Jaeger query
- [x] add trace export/query/integration assertions and failure tests
- [x] verify gates and update docs/ADR/learning trace artifact

## Progress log
- 2026-10-01: opened after ExecPlan 0004 passed 27 Python tests, 5 Java tests, nine-service Compose boot, MCP smoke, healthy smoke, and S1 approval/restart/recovery. Official OpenTelemetry Python exporter/instrumentation and Jaeger 2.21 docs confirm OTLP/HTTP ingest on 4318 and Jaeger query APIs on 16686; exact v3 query shape still to be verified.
- 2026-10-01: verified Jaeger v3 `query.serviceName`, `query.operationName`, required RFC3339 time bounds, and OTLP `resourceSpans` using the live container. Pinned SDK 1.45, Jaeger 2.21.0, and Java agent 2.31.1 with SHA-256 check. Fixed a global TracerProvider collision by using an explicit local provider for RAL spans. Added bounded Trace MCP queries and W3C context forwarding for the approved reset.
- 2026-10-01: `make lint test compose-check mcp-smoke smoke-test scenario SCENARIO=redis-unavailable` passed (30 Python tests, 5 Java tests). S1 printed run trace `c15e2cd00a4b2ce88e32a6c0f8c83d3a` and resume trace `979481c9d817479d32a5d9457267e131`; `verify_traces.py` proved the Java reset span's parent is Python `tool.reset_redis_fault`. Jaeger storage is in-memory, so those IDs are temporary.

## Decisions / discoveries
- SSE events are not spans. The Trace specialist's current `available=false` result is honest but leaves Goal verification item 6 open.
- Jaeger all-in-one uses transient in-memory storage; a restart may erase demo traces, so verification must query while the stack remains up.

## Verification
Passed `make dev-up` after rebuilding the instrumented stack, then `make lint test compose-check mcp-smoke smoke-test scenario SCENARIO=redis-unavailable`. `scripts/verify_traces.py` is invoked by S1 and queries the Jaeger v3 API for incident/run and resumed traces, parent relationships, Java order-read evidence, and cross-service reset parentage. Unit tests distinguish empty and unavailable Jaeger responses.

## Remaining risks / follow-ups
S2–S4, inventory/payment services, semantic replan, evaluation report, and v0.1.0 release criteria remain after this plan.
