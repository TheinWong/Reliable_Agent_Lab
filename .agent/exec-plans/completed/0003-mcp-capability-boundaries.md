# ExecPlan 0003 — MCP Capability Boundaries (completed)

## Objective
Replace the Python specialists' direct HTTP adapters with standard MCP servers/clients that expose separate typed metrics, logs, traces, and constrained operations capability groups. Keep read-only investigation permissions separate from mutations and preserve the verified S1 behavior.

## Relevant repository context
Read:
- `AGENTS.md` and `CODEX_GOAL.md`
- `docs/10-architecture/MCP_AND_TOOL_BOUNDARIES.md`
- `docs/10-architecture/MULTI_AGENT_DESIGN.md`
- `docs/10-architecture/STATE_AND_HANDOFFS.md`
- `docs/20-engineering/RELIABILITY_AND_SAFETY.md`
- `docs/20-engineering/API_CONVENTIONS.md`
- `docs/20-engineering/TESTING_STRATEGY.md`
- `docs/50-roadmap/ROADMAP.md`
- completed ExecPlans 0001 and 0002; current capability ports, graph, Java evidence/fault APIs, Compose and S1 script

## Acceptance criteria
- at least three real MCP capability groups are running in Compose, including read-only investigation and constrained operations; target four groups: metrics, logs, traces, operations;
- each tool has validated input/output, timeout, clear error taxonomy, documented read-only/mutating flag, and contract tests;
- Metrics, Logs, and Trace specialists only receive clients for their assigned server and cannot call operations through their injected interfaces/configuration;
- operations server exposes only named demo actions needed for scenarios, with a local-demo scope guard and policy/idempotency hook; no arbitrary shell, SQL, URL, or Docker command tool;
- the S1 multi-agent graph gets real metrics/log evidence through MCP and retains honest trace-unavailable behavior until the trace backend is implemented;
- Java fault endpoint is no longer called directly by the investigation graph; the existing scenario injector remains separate from agent operations until remediation/HITL is implemented;
- tool calls/errors appear as stable API/SSE events without leaking credentials or unbounded payloads;
- Python lint/type/tests, Java tests, Compose boot, smoke, and S1 scenario pass;
- README, roadmap, ADR, walkthrough, and learning notes match observed behavior.

## Non-goals
- allowing automatic remediation or bypassing future risk/HITL policy;
- declaring Trace spans available before a real backend exists;
- durable checkpoint/resume;
- adding another agent framework or general infrastructure control.

## Design / approach
Use the official MCP Python SDK with its documented server and client transports. Put one capability group per server boundary and inject per-role client objects into the existing specialist ports. Keep contracts Pydantic-validated at both sides and implement a typed error result/status rather than folding transport failures into empty success. The operations server is a constrained demo adapter but is not passed to read-only agents or invoked by the current Supervisor graph. Add contract tests that exercise the MCP transport, permission split, timeout/dependency errors, and idempotency preconditions.

## Work breakdown
- [x] inspect current SDK/transport APIs and choose pinned compatible version
- [x] define tool contracts and error taxonomy
- [x] implement metrics/logs/traces MCP servers
- [x] implement scoped operations MCP server with policy/idempotency hook
- [x] implement role-specific MCP clients replacing HTTP adapters
- [x] wire Compose health/config and API events for tool calls
- [x] add transport/contract/security/failure tests
- [x] run S1 and full regression gates
- [x] update docs, roadmap, ADR, and learning artifacts

## Progress log
- 2026-09-30: opened after ExecPlan 0002 passed 8 Python tests, 5 Java tests, Compose build/health, smoke, and S1 with three specialist reports and SSE delegation evidence.
- 2026-09-30: pinned `mcp==2.2.0`, added four separate Streamable HTTP servers and role-specific clients, scoped reset, typed errors, SSE tool events, Compose and CI checks. A log assertion using `grep -q` under `pipefail` intermittently exited on SIGPIPE as output grew; changed it to consume the bounded log stream. Repeated S1 passed.
- 2026-09-30: final verification: `make lint test` passed (14 Python and 5 Java tests), then added malformed-payload regression and `make lint python-test` passed (15 Python tests). `make compose-check dev-up` completed with eight healthy services; `make mcp-smoke`, `make smoke-test`, and `make scenario SCENARIO=redis-unavailable` passed after rebuilding latest runtime code. Documentation and ADR-008 updated.

## Decisions / discoveries
- The Trace capability must return an explicit unavailable result until a real Jaeger-backed source exists. No synthetic span evidence will be claimed.
- Operations transport is introduced before execution wiring so its mutation surface can be tested independently of the remediation/HITL graph.
- The server-side duplicate ledger is process-local, while the Java reset endpoint is idempotent. Durable operation idempotency and approval-gated graph usage remain future work.

## Verification
Passing commands: `make lint test` (14 Python, 5 Java), `make lint python-test` after the final contract test (15 Python), `make compose-check dev-up` (eight healthy services), `make mcp-smoke`, `make smoke-test`, and `make scenario SCENARIO=redis-unavailable`. Real MCP transport and policy coverage is in `tests/test_mcp_contracts.py` and `mcp_smoke.py`. These are local checks; GitHub Actions has not run on a remote.

## Remaining risks / follow-ups
- The next plan must add Remediation Agent, independent Verifier Agent, risk policy and HITL; operations must not be auto-used before those gates exist.
- Durable checkpointing, real trace backend, and S2-S4 remain top-level Goal requirements.
