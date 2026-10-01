# ExecPlan 0002 — Real Multi-Agent Investigation

## Objective
Replace the foundation workflow with a real LangGraph Supervisor that delegates independent work to Metrics, Logs, and Trace specialist agents in parallel, then fuses typed reports into a diagnosis without granting investigation agents mutating capabilities.

## Relevant repository context
Read:
- `docs/10-architecture/MULTI_AGENT_DESIGN.md`
- `docs/10-architecture/STATE_AND_HANDOFFS.md`
- `docs/10-architecture/MCP_AND_TOOL_BOUNDARIES.md`
- `docs/20-engineering/RELIABILITY_AND_SAFETY.md`
- `docs/20-engineering/OBSERVABILITY.md`
- `docs/30-scenarios/EVALUATION_METRICS.md`
- completed ExecPlan 0001 and current graph/evidence code

## Acceptance criteria
- Supervisor, Metrics, Logs, and Trace roles are distinct graph nodes/components with explicit responsibilities and tool allowlists;
- specialists receive role-scoped input rather than the entire mutable application state;
- Metrics/Logs/Trace produce validated `SpecialistReport` contracts with evidence references, confidence, hypotheses, and missing information;
- independent specialists execute concurrently and a deterministic test proves fan-out/fan-in rather than sequential naming;
- S1 runs through the multi-agent topology and produces a root-cause diagnosis referencing actual metrics/log/fault evidence; Trace may explicitly report unavailable/not-required for S1 but must not fabricate spans;
- read-only investigation failures are typed, bounded, visible to Supervisor, and do not silently become empty success;
- API/SSE surfaces typed delegation/report/diagnosis events without exposing hidden reasoning;
- unit, integration, smoke, and S1 regression checks pass;
- architecture, roadmap, walkthrough, trace boundary, and interview notes reflect only verified behavior.

## Non-goals
- mutating Operations MCP;
- Remediation Agent or Verifier Agent;
- HITL approval and durable restart/resume;
- all four final scenarios;
- pretending that internal adapters are already MCP servers.

## Design / approach
Use deterministic specialist policies first so CI requires no model credentials. Keep each specialist behind a narrow capability protocol and pass a compact immutable task containing incident identity, service, symptom, and allowed evidence window. Use LangGraph parallel fan-out with an ID-aware reducer for specialist reports/evidence, followed by Supervisor fusion. Treat Trace as a real role with an honest unavailable/not-required report until trace infrastructure supplies evidence. Preserve the existing incident API shape where practical and emit a stable event projection.

## Work breakdown
- [x] inspect plan-scoped architecture/observability/evaluation documents
- [x] stabilize incident/report/error contracts and reducers
- [x] define role-scoped specialist tasks and capability interfaces
- [x] implement Metrics, Logs, and Trace specialists
- [x] implement parallel LangGraph fan-out/fan-in Supervisor
- [x] project delegation/report/diagnosis events to API/SSE
- [x] add concurrency, reducer, failure, and diagnosis tests
- [x] route real S1 through the multi-agent graph
- [x] run full regression and update docs/roadmap

## Progress log
- 2026-09-30: created after ExecPlan 0001 passed Python/Java/unit/Compose/smoke/S1 evidence and moved to `completed/`.
- 2026-09-30: added bounded read-only metrics/log evidence endpoints in order-service; each specialist receives only its own capability object and a compact immutable task. The Trace role reports `unavailable` until a real backend exists.
- 2026-09-30: replaced the foundation graph with Supervisor fan-out to Metrics/Logs/Trace and fan-in to typed report fusion. Added role-ID reducer, typed failure reports, stable delegation/diagnosis SSE events, and a barrier test that fails if specialists run sequentially. Ruff, strict mypy, and 8 Python tests passed.
- 2026-09-30: rebuilt Java 21 and Python containers; integrated S1 returned a diagnosis with all three specialist reports, real metrics/log evidence references, and 3 delegation start/completion event pairs. Added script assertions to make this an automated regression gate; final rerun after latest script/code changes remains pending.
- 2026-09-30: added explicit `run_id` correlation to API resources/events and LangGraph invocation config, and hardened Logs Agent against stale failures from an earlier fault cycle. A deterministic stale-log test now requires insufficient evidence for that case.
- 2026-09-30: final rerun passed `make lint python-test compose-check`, Java 21 container build with 5 JUnit tests, four-service health wait, `make smoke-test`, and `make scenario SCENARIO=redis-unavailable`. The scenario asserts three typed reports, evidence refs, and three delegation start/completion SSE pairs.
- 2026-09-30: a transient Maven Central TLS handshake interrupted one rebuild before tests; the identical retry resolved dependencies and completed successfully. No code or dependency changes were made to hide it.

## Decisions / discoveries
- S1 does not require fabricated trace data. Trace Agent must return a typed statement that trace evidence is unavailable or unnecessary for this scenario while Metrics and Logs provide real evidence.
- Logs Agent only counts cache read failures after the most recent active fault injection; old failures across a reset must not confirm a new fault.
- MCP conversion remains the following ExecPlan so this plan can prove role/context/concurrency semantics before adding transport complexity. Capability protocols must nevertheless match the future permission boundary.

## Verification
- `make lint python-test compose-check` — Ruff, strict mypy, 8 Python tests, and Compose config passed after the latest change.
- `docker compose up -d --build --wait --wait-timeout 240` — Java 21 build and 5 Java tests passed; all four containers healthy.
- `make smoke-test` and `make scenario SCENARIO=redis-unavailable` — passed after stronger report/SSE assertions.
- Manual S1 incident read and SSE showed real Metrics/Logs report evidence, honest Trace unavailable report, three delegation starts/completions, and diagnosis event.
- `git diff --check` and shell syntax checks passed.

## Remaining risks / follow-ups
- Direct HTTP capability adapters remain temporary until MCP extraction.
- Real Jaeger trace evidence is required by a later observability ExecPlan and the top-level Goal.
