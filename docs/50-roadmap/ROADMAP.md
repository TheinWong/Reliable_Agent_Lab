# Roadmap

The top-level Codex Goal is the v0.1.0 public MVP. Build in vertical slices and keep the repository runnable.

## Phase 0 — Repository foundation
- [x] build/lint/test tooling scaffolding
- [x] Docker Compose baseline
- [x] docs/Makefile/env conventions
- [x] CI baseline

## Phase 1 — Demo microservices and telemetry
- [x] order/inventory/payment services and checkout-preview HTTP path
- [x] MySQL/Redis integration for order-service
- [x] Actuator/Prometheus hooks, bounded logs, and Java order-service tracing for S1
- [x] deterministic Redis fault injection API and reset
- [x] first Redis scenario
- [x] controlled MySQL-read fault, metrics/logs, and automated S2 recovery scenario (not a physical database outage or pool exhaustion)
- [x] controlled S3 inventory latency and S4 payment-preview HTTP 5xx with real downstream traces

## Phase 2 — Single vertical agent flow foundation
- [x] first-slice domain models/state
- [x] FastAPI incident create/read/events API (now PostgreSQL-backed)
- [x] minimal deterministic LangGraph flow
- [x] deterministic fake-tool tests

## Phase 3 — Multi-agent investigation
- [x] Supervisor delegation and deterministic evidence fusion for S1–S4
- [x] Metrics Agent with read-only metrics capability
- [x] Logs Agent with read-only bounded log capability
- [x] Trace Agent with bounded Jaeger-backed order-read evidence and explicit empty/unavailable results
- [x] parallel fan-out/fan-in
- [x] structured specialist reports

## Phase 4 — MCP tool layer
- [x] bounded metrics tool through MCP
- [x] bounded logs tool through MCP
- [x] read-only trace MCP tool backed by bounded Jaeger v3 queries
- [x] constrained local-demo reset tool through a separate operations MCP server, invoked only after approval
- [x] transport, contract, permission, and error tests

## Phase 5 — Remediation and verification
- [x] deterministic S1–S4 Remediation Agent with typed plans
- [x] fail-closed policy requiring approval for S1–S4 mutation
- [x] API approval plus LangGraph interrupt/resume for S1–S4
- [x] independent fresh-read Verifier Agent for S1–S4
- [ ] replan path

## Phase 6 — Reliable execution
- [x] timeout/error classification and bounded two-attempt transient operation retry for S1
- [x] PostgreSQL graph checkpoints plus durable incident/event resources
- [x] duplicate approval guard, stable S1 action ID, and PostgreSQL action-result ledger; general exactly-once external effects remain open
- [x] acyclic graph and explicit recursion limit
- [x] S1–S4 approval pause, agent-api restart, resume, and recovery integration scripts

## Phase 7 — Observability and evaluation
- [x] OpenTelemetry spans for S1–S4 agent/tool/Java reset boundaries
- [x] Jaeger S1–S4 traces with automated query and parent-link assertions
- [x] order-service Prometheus-format metrics endpoint and four-case evaluation; dashboards remain future work
- [x] four automated ground-truth scenarios (clean local replay and hosted CI verified)
- [x] exact four-case persisted-incident evaluation script (`make evaluate`); no statistical generalization

## Phase 8 — Open-source polish / v0.1.0
- [x] verified clean-checkout quick start (local replay at `0f3f676`)
- [x] architecture flow diagram/docs aligned with S1–S4
- [x] learning artifacts for code/graph/trace walkthrough
- [x] security/contributing docs with local-demo scope and disclosure guidance
- [x] v0.1.0 MVP acceptance checklist green (clean local replay and hosted CI; evidence in `VERIFICATION_AUDIT.md`)
- [ ] optional owner-authorized `v0.1.0` tag and GitHub Release (not part of the verified code MVP)
