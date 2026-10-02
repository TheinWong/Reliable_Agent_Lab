# Reliable Agent Lab

> A production-oriented multi-agent tool-using system built with LangGraph, MCP and FastAPI, validated through reproducible microservice incident diagnosis and recovery.

**Status:** v0.1.0 public MVP code is on GitHub. S1–S4 have passed both clean local replay and hosted GitHub Actions, including parallel MCP investigation, approval-gated remediation, independent recovery checks, restart/resume, and real Jaeger spans. No version tag or GitHub Release has been published.

## Why this project
Reliable Agent Lab is an open-source engineering project for demonstrating how multiple specialized agents can collaborate safely over real tools while remaining observable, recoverable and testable.

The project focuses on:
- multi-agent orchestration rather than chatbot UX;
- explicit state and handoffs;
- context/tool permission isolation;
- MCP integrations;
- Python agent-backend engineering;
- Java microservice integration;
- reliable side effects and human approval;
- tracing and scenario-driven verification.

The first domain is microservice incident handling because it provides real evidence, tools, failure modes and measurable recovery criteria. The repository is not intended to be a general SRE product.

## Runtime architecture

```text
Alert / Scenario
      |
      v
 FastAPI Incident API
      |
      v
 Supervisor Agent
   /    |     \
  v     v      v
Metrics Logs  Trace       (parallel, read-only specialists)
  \     |      /
   \    |     /
    v   v    v
 Supervisor evidence fusion
      |
      v
 Remediation Agent
      |
   Risk Policy (all local mutations high risk)
      |
   Human Approval / persisted checkpoint
      |
   Operations MCP
             |
             v
        Demo Services
             |
             v
        Verifier Agent
          /      \
     resolved   unresolved
```

## Stack
- Python 3.12, LangGraph, Pydantic
- FastAPI, asyncio, SSE
- MCP Python SDK
- Java 21, Spring Boot, MySQL, Redis
- Prometheus-format Actuator metrics, OpenTelemetry, Jaeger
- PostgreSQL for durable workflow state where required
- Docker Compose, GitHub Actions

## Documentation map
See [`docs/INDEX.md`](docs/INDEX.md).
See [`CHANGELOG.md`](CHANGELOG.md) for the local v0.1.0 candidate scope and limitations.

Codex should use [`AGENTS.md`](AGENTS.md) as the short repository contract and [`CODEX_GOAL.md`](CODEX_GOAL.md) as the v0.1.0 completion contract.

## Locally verified quick start

Prerequisites: Git, Docker Engine/Desktop with Compose v2, Python 3 for shell assertions, and `uv` for the scenario trace verifier and local checks. Application builds use pinned Python 3.12 and Java 21 containers.

```bash
cp .env.example .env
make dev-up
make mcp-smoke
make smoke-test
make scenario SCENARIO=redis-unavailable
make scenario SCENARIO=mysql-unavailable
make scenario SCENARIO=inventory-latency
make scenario SCENARIO=payment-5xx
make evaluate
make dev-down
```

The smoke test proves an order read populates Redis, a second read hits the cache, and the FastAPI/LangGraph incident workflow completes. S1 injects a controlled Redis failure and proves MySQL fallback. S2 injects a controlled MySQL read failure for an uncached order and proves the explicit HTTP 503. S3 injects an 800 ms inventory delay; S4 injects a payment-preview HTTP 503 that causes an upstream 502. All four scenarios pause after parallel diagnosis, restart the agent API, approve a typed reset plan, check independent recovery, retry approval without a second operation, and query Jaeger for real Python/Java spans. S3/S4 additionally prove the downstream failure span belongs to the order-preview trace. The scenarios print trace IDs; open Jaeger at `http://127.0.0.1:16686` while the stack is running. S2 simulates a read fault at the application boundary; it does not stop MySQL or exhaust a real connection pool. S4 makes no actual charge.

`make evaluate` reads the latest persisted incident for each machine-readable scenario fixture and reports exact pass/fail checks. It is a four-case regression summary, not a statistically general benchmark.

## Development checks

```bash
uv sync --frozen
make lint
make python-test
make java-test
make compose-check
```

`make java-test` runs both Java service test suites in a Java 21 container. Core tests and S1–S4 do not require an LLM API key.

The v0.1.0 incident workflow is deterministic: it makes no live LLM API calls and incurs no model-token cost. A live-model adapter remains future, optional work.

## Implemented now

- typed FastAPI incident create/read/SSE/approval endpoints with PostgreSQL-backed resources and events;
- a deterministic LangGraph Supervisor with parallel Metrics, Logs, and Trace specialist nodes, typed reports, and role-scoped MCP clients;
- four MCP servers for metrics, logs, traces, and local-demo operations; read-only specialists do not receive the mutating client;
- a deterministic Remediation Agent, fail-closed risk policy, LangGraph approval interrupt and PostgreSQL checkpoint, constrained Operations MCP execution, and independent Verifier Agent;
- Spring Boot order reads with MySQL as source of truth and explicit Redis cache-aside fallback;
- local-demo-only, idempotent Redis, controlled MySQL-read, inventory-latency and payment-5xx fault injection/reset;
- a real checkout-preview path from order-service through inventory-service and a stateless payment authorization preview;
- Actuator/Prometheus hooks, structured fault/cache logs, OpenTelemetry/Jaeger spans, Docker Compose health checks;
- Python and Java unit tests plus automated S1–S4 scenarios.

The Trace MCP server reads bounded recent order and checkout-preview traces from Jaeger and distinguishes empty results from backend failure. S1–S4 resets are idempotent and approval-gated in this local demo, with a PostgreSQL action-result ledger; there is no production authentication or general exactly-once guarantee across arbitrary external effects. Replan after failed verification and full trace continuity for every read-only tool remain out of scope. See [`docs/50-roadmap/ROADMAP.md`](docs/50-roadmap/ROADMAP.md).

## License
MIT.
