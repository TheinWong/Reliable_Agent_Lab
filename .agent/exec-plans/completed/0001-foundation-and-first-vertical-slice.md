# ExecPlan 0001 — Foundation and First Vertical Slice

## Objective
Create a runnable repository foundation and one end-to-end thin slice that proves the architecture can support a faultable Spring Boot service plus a Python incident workflow, without attempting every v0.1 feature at once.

## Relevant context
Read:
- `CODEX_GOAL.md`
- `docs/00-product/*`
- `docs/10-architecture/SYSTEM_ARCHITECTURE.md`
- `docs/10-architecture/BACKEND_AND_INFRA.md`
- `docs/20-engineering/CODING_STANDARDS.md`
- `docs/20-engineering/TESTING_STRATEGY.md`
- `docs/30-scenarios/SCENARIO_CATALOG.md`

## Acceptance criteria
- repository has working Python and Java build/test/lint scaffolding;
- Docker Compose baseline starts core dependencies/services needed for the slice;
- at least `order-service` is functional with Redis/MySQL and telemetry hooks;
- Redis fault can be injected and reset deterministically;
- FastAPI can create an incident;
- a minimal LangGraph state/workflow can collect deterministic health/log evidence through temporary internal adapters or mocks;
- smoke/integration tests verify the thin slice;
- CI baseline exists;
- docs/roadmap/progress reflect actual status.

## Non-goals
- full multi-agent specialization;
- complete MCP conversion;
- durable HITL;
- all demo microservices;
- all scenarios.

## Approach
Implement the smallest vertical architecture-compatible slice, keeping interfaces ready for later specialist/MCP extraction. Prefer real demo-service behavior plus deterministic fake model behavior in CI.

## Work breakdown
- [x] inspect package/docs and toolchain availability
- [x] initialize repository/build structure
- [x] Python tooling/API skeleton/tests
- [x] Java order-service + Redis/MySQL/tests
- [x] telemetry/fault-injection hooks
- [x] Compose baseline
- [x] first Redis fault scenario definition + scripts/tests
- [x] minimal incident state/graph/API
- [x] smoke/integration test
- [x] CI
- [x] update walkthrough/roadmap

## Progress log
- 2026-09-30: unpacked the supplied scaffold into an independent project root, initialized local Git, committed the import baseline, and created `codex/execplan-0001-foundation`.
- 2026-09-30: verified Git 2.39.5, Python 3.12.8, Maven 3.9.16, Docker 28.0.4, Compose 2.34.0, and a running Docker daemon. The host has Java 24/27 rather than Java 21, so Java 21 compatibility will be enforced by Maven release configuration and the Java 21 build/runtime container.
- 2026-09-30: read the plan-scoped product, architecture, engineering, and scenario documents. Implementation starts with stable typed contracts and a deterministic fake/control path; live model credentials are not required.
- 2026-09-30: implemented a locked Python 3.12 package with FastAPI, typed incident/evidence contracts, SSE event projection, a deterministic LangGraph, timeout-bounded order-service evidence adapter, and tests. `make lint python-test` passed with Ruff, strict mypy, and 4 pytest tests.
- 2026-09-30: implemented Java 21/Spring Boot 3.5.16 order-service with MySQL-authoritative explicit Redis cache-aside behavior, Actuator/Prometheus hooks, structured degraded logs, and demo-only idempotent fault controls. Containerized `mvn -B -ntp verify` passed 3 tests.
- 2026-09-30: added the four-service Compose baseline, health checks, S1 machine-readable ground truth, smoke/scenario scripts, and three-job CI. `docker compose up -d --build --wait`, `make smoke-test`, and `make scenario SCENARIO=redis-unavailable` passed twice; S1 verified MySQL fallback and post-reset database-populate/cache-hit behavior.
- 2026-09-30: synchronized README, roadmap, ADRs, project/trace walkthroughs, and interview notes with the verified boundary. Multi-agent, MCP, durable HITL/resume, full tracing, and remaining scenarios remain explicitly unclaimed.

## Decisions / discoveries
- The delivered directory was nested inside a dirty parent repository. It is now an independent local Git repository so project work cannot accidentally include or modify parent changes.
- `python3` resolves to 3.13.3, but `/usr/local/bin/python3.12` provides the required Python 3.12.8. Project commands must use a project virtual environment created from Python 3.12 (or the Python 3.12 container).
- The first slice will use a real Spring Boot/MySQL/Redis service and deterministic incident orchestration. The Redis fault is exposed only through a local-demo-scoped typed endpoint, and order reads fall back to authoritative MySQL while surfacing degraded cache evidence.

## Verification
- `make lint` — Ruff format/check and strict mypy passed.
- `make python-test` — 4 passed.
- `make java-test` — Spring Boot build and 3 tests passed under Java 21 container.
- `make compose-check` — Compose model valid.
- `make dev-up` — MySQL, Redis, order-service, and agent-api built and became healthy.
- `make smoke-test` — healthy database-to-cache path and incident workflow passed.
- `make scenario SCENARIO=redis-unavailable` — injection, degraded read, diagnosis, structured log, reset, repopulation, and cache hit passed.
- `bash -n scripts/lib.sh scripts/smoke.sh scripts/scenarios/redis-unavailable.sh` and `git diff --check` passed.

## Remaining risks / follow-ups
- The incident store/task registry is process-local and intentionally not restart-safe; durable checkpoint/resume is a later Goal criterion.
- The current graph is deterministic and single-workflow, not the required multi-agent topology. The next ExecPlan introduces Supervisor plus Metrics/Logs/Trace specialists with typed fan-out/fan-in.
- HTTP evidence adapters are temporary and must be replaced with permission-scoped MCP capability groups.
- Prometheus-compatible metrics and structured logs exist, but the required OpenTelemetry/Jaeger agent/tool trace does not.
- Only S1 is automated; S2-S4 and inventory/payment services remain future work.
