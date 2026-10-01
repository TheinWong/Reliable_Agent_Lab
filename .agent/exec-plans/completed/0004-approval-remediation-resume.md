# ExecPlan 0004 — Approval-Gated Remediation and Durable Resume (completed)

## Objective
Extend the S1 graph beyond diagnosis with a distinct Remediation Agent, server-side risk policy, a real approval pause, an operations MCP call, and independent fresh-evidence Verifier Agent. Persist enough incident/event/graph/action state in PostgreSQL for an approval-paused incident to resume after agent-api restart without duplicate mutation.

## Relevant repository context
`AGENTS.md`, `CODEX_GOAL.md`, `.agent/PLANS.md`; `docs/10-architecture/{MULTI_AGENT_DESIGN,STATE_AND_HANDOFFS,MCP_AND_TOOL_BOUNDARIES}.md`, `docs/20-engineering/{RELIABILITY_AND_SAFETY,API_CONVENTIONS,TESTING_STRATEGY}.md`; `src/reliable_agent_lab/{models,graph,service,api,evidence,mcp_server}.py`; `compose.yaml`; S1 script and tests.

## Acceptance criteria
- S1 with confirmed Redis fault yields a typed remediation plan, independent policy decision, and `approval.required` state/event before any operations MCP call.
- An approval endpoint validates a pending action identity; denial ends safely with no mutation, duplicate approval is idempotent/conflict-safe, and approval resumes a paused LangGraph thread.
- PostgreSQL-backed graph checkpoint and incident/event/action records survive agent-api restart; integration test pauses, restarts, approves, and verifies completion.
- The Remediation Agent proposes only the named reset action; the execution boundary invokes only the operations MCP server after approval, with a stable action idempotency key and retry-safe record.
- The Verifier Agent collects fresh service evidence after execution, checks fault reset plus database repopulation and cache hit independently of the operation result; it can report unresolved.
- Explicit timeout/error classes, bounded transient retry, and an unresolved verifier outcome are tested; no unapproved or unsupported action is executed. Semantic replan remains a separate Goal item.
- Python/Java checks, Compose boot, smoke, and S1 pass; docs/ADR/learning notes match actual behavior.

## Non-goals
No arbitrary infrastructure control, production authorization service, real Jaeger traces, or S2–S4 implementation. No claim of exactly-once delivery under all crash timings without a durable operation ledger and recovery test.

## Design / approach
Use LangGraph `interrupt`/`Command(resume=...)` and `AsyncPostgresSaver` with a stable run/thread id. Keep policy outside the Remediation Agent. Persist API-facing incident/events/action data in PostgreSQL rather than reconstructing them solely from in-memory tasks. Place side effects in their own graph node and make the operation/action record idempotent. Reuse the constrained operations MCP tool; Verifier uses fresh read-only service evidence. Test restart from the API boundary, not only checkpoint serialization.

## Work breakdown
- [x] define typed plan, approval, execution, and verification models plus policy
- [x] add PostgreSQL checkpointer and durable incident/event/action store
- [x] add remediation, approval interrupt, constrained execute, and verifier graph nodes
- [x] add approval API and restart-safe task lifecycle
- [x] add duplicate/denial/timeout/fresh-evidence tests
- [x] integrate S1 approval/recovery and restart scenario
- [x] run final gates and update docs/ADR/learning artifacts

## Progress log
- 2026-09-30: opened after ExecPlan 0003 passed 15 Python tests, 5 Java tests, eight-service Compose health, MCP smoke, API smoke, and S1. Read the relevant repository contracts and official LangGraph persistence API; `.setup()` is required on first use for `AsyncPostgresSaver`.
- 2026-09-30: added PostgreSQL-backed API incident/event store alongside LangGraph `AsyncPostgresSaver`, Compose PostgreSQL, and app lifespan setup. `make lint python-test compose-check` passed; rebuilt nine-service Compose, smoke passed, then restarted agent-api and retrieved the same completed incident and 16 SSE events from the new process. Added typed deterministic remediation plan/risk policy and a separate fresh-read verifier probe contract; 18 Python tests currently pass. Graph interrupt, approval endpoint, execution, and verifier routing are still open.
- 2026-10-01: wired typed S1 graph plan/policy/interrupt/execution/verifier nodes, approval API, persisted decision and startup replay, and fresh recovery probe. Unit/API/graph tests now cover pre-approval no-mutation, denial, duplicate approval, stable action ID, transient retry, unresolved verification, recovery when a decision was saved before task launch, and final-checkpoint reconciliation. `make lint python-test` passed (26 tests). Nine-service Compose boot, MCP smoke, healthy smoke, and S1 scenario passed; S1 restarts agent-api while paused, approves, verifies DB-to-cache recovery, and repeats approval without another operation event. Documentation/ADR updates in progress; full final gate pending.
- 2026-10-01: added PostgreSQL action execution records with a started/completed/failed lifecycle; a completed record short-circuits replay of the Operations MCP call. Added a graph-replay ledger test and S1 database row assertion. `make lint python-test compose-check` passed (27 Python tests); rebuilt Compose and rerun of the full scenario pending.
- 2026-10-01: rebuilt the nine-service Compose stack and reran S1 with a paused-process restart, approval, fresh Verifier evidence, duplicate-approval operation-event count, and one PostgreSQL action row; passed. `make mcp-smoke` and `make smoke-test` passed on the rebuilt stack. Final lint/Python/Java/Compose gate is running.
- 2026-10-01: final gate `make lint test compose-check` passed: Ruff formatting/lint, strict mypy, 27 Python tests, 5 Java tests, and Compose validation. A final duplicate/conflicting-approval assertion kept `make lint python-test` green (27 tests). S1, MCP smoke, and healthy smoke passed against the rebuilt runtime. No remote is configured, so CI workflow configuration was checked locally but no hosted GitHub Actions run is claimed.

## Decisions / discoveries
- Current incident resources/events and task registry are process-local, so adding a graph checkpointer alone would not meet API-level restart/resume.
- An operation response is not verification; the verifier must observe fresh cache behavior.
- `probe_cache_recovery` checks fault state and two order GETs. S1 clears the demo cache key before fault injection, so the expected post-reset sources are `DATABASE` then `CACHE`; this probe is not a general production cache audit.
- The current idempotency boundary is a persisted duplicate-approval decision, a stable per-incident action ID, a PostgreSQL action outcome, a process-local Operations ledger, and an idempotent Java reset. A crash after the external call but before ledger completion may retry that idempotent reset; this is not general exactly-once side-effect execution.

## Verification
Passing local commands: `make lint test compose-check` (27 Python, 5 Java), `make dev-up` (nine healthy services), `make mcp-smoke`, `make smoke-test`, and `make scenario SCENARIO=redis-unavailable`. S1 itself pauses, restarts agent-api, retrieves the same incident/SSE history, approves, verifies recovery, repeats approval, asserts only one remediation operation event, and confirms one action-ledger row. Hosted GitHub Actions has not run because this local repository has no remote.

## Remaining risks / follow-ups
S2–S4, real trace backend/OTel spans, additional Java services, semantic replan, and release polishing remain top-level Goal requirements. The demo's unauthenticated approval API is not production-ready; the idempotent Java reset plus ledger do not establish exactly-once effects for arbitrary operations.
