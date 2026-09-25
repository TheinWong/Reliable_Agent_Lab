# Reliable Agent Lab

> A production-oriented tool-using agent built with LangGraph, MCP, and FastAPI, demonstrated through reproducible microservice incident diagnosis and recovery.

**Status:** Milestone 1 - faultable Spring Boot service

Reliable Agent Lab is an open-source engineering project for learning and demonstrating how tool-using agents can execute real-world tasks reliably, safely, and observably.

The project intentionally does **not** focus on building another chatbot, RAG demo, or prompt-only agent. Its focus is the runtime and backend engineering behind production agent systems:

- explicit state and workflow orchestration;
- structured tool calling;
- MCP-based tool integration;
- asynchronous execution;
- human approval for risky actions;
- checkpoint, interrupt, and resume;
- retry, replan, and post-action verification;
- typed tool contracts and structured model output;
- tracing and observability;
- integration between a Python agent service and a Java/Spring Boot backend.

The first reproducible environment is a small fault-injectable Spring Boot Order Service backed by MySQL and Redis.

## Why this project?

A production agent must handle more than a successful LLM response. It must answer questions such as:

- What state must survive between execution steps?
- What happens when a tool times out?
- Which actions may execute automatically?
- Which actions require human approval?
- How does a workflow resume after a process restart?
- How do we prevent duplicated side effects?
- How do we verify that an action actually solved the problem?
- How can the full execution trajectory be inspected and tested?

Reliable Agent Lab makes these concerns explicit in code, contracts, policies, tests, and traces.

## Project boundaries

### In scope

- Python 3.12
- LangGraph
- Pydantic
- FastAPI
- asyncio and SSE
- MCP Python SDK v2
- Java 21 + Spring Boot
- MySQL + Redis
- Prometheus
- OpenTelemetry + Jaeger
- Docker + Docker Compose
- pytest + JUnit
- GitHub Actions

### Not a V1 focus

- RAG
- long-term memory
- multi-agent orchestration
- fine-tuning or RLHF
- local LLM hosting
- Kubernetes
- a complex frontend

These can be explored later only if they serve a concrete engineering requirement.

## Target architecture

```text
                       Remote LLM API
                             ^
                             |
                       +-----+------+
                       | FastAPI    |
                       | Agent API  |
                       +-----+------+
                             |
                       +-----v------+
                       | LangGraph  |
                       | Runtime    |
                       +-----+------+
                             |
                         MCP Client
                             |
             +---------------+---------------+
             |               |               |
             v               v               v
      Observability MCP  Database MCP   Operations MCP
             |               |               |
             +---------------+---------------+
                             |
                             v
                      Spring Boot Service
                             |
                    +--------+--------+
                    |                 |
                    v                 v
                  MySQL             Redis

Spring Boot Actuator --> Prometheus
Agent / service traces --> OpenTelemetry --> Jaeger
LangGraph checkpoints --> SQLite first, PostgreSQL later
```

## Agent workflow

```text
Incident
   |
   v
Collect Evidence
   |
   v
Diagnose
   |
   v
Create Remediation Plan
   |
   v
Risk Check
   |
   +--------------------+
   |                    |
   v                    v
Low Risk            High Risk
   |                    |
   v                    v
Execute           Human Approval
   |                    |
   +----------+---------+
              |
              v
            Verify
          /        \
      Success     Failure
         |           |
         v           v
        END        Replan
```

Traditional monitoring or deterministic scenario scripts are responsible for detecting abnormal conditions. The agent is responsible for investigation, diagnosis, planning, safe action execution, and verification.

## Demo environment

The first environment is a small Spring Boot Order Service. MySQL is the source
of truth and Redis provides cache-aside order-detail caching. Redis failures are
visible through health, structured logs, and bounded-label Prometheus metrics,
while existing orders remain readable through a timeout-bounded MySQL fallback.

Start the environment and run the verified Redis-unavailable scenario:

```bash
docker compose -f infra/docker-compose.yml up -d --build
./scenarios/redis-unavailable/verify.sh
```

The scenario script verifies healthy cache behavior, a real Redis outage,
business API continuity, diagnostic evidence, and application-level recovery.

Scenario status:

1. Redis timeout / unavailable — implemented
2. MySQL connection failure
3. artificial request latency
4. HTTP 5xx fault
5. connection pool exhaustion
6. downstream timeout
7. cache inconsistency
8. bad configuration

Each scenario must define:

- deterministic fault injection;
- expected external symptoms;
- observable evidence;
- ground-truth root cause;
- expected remediation;
- verification criteria.

## Repository structure

```text
.
├── agent/                  # LangGraph runtime
├── api/                    # FastAPI service
├── mcp-servers/            # MCP tool servers
├── demo-service/           # Spring Boot target service
├── scenarios/              # Reproducible fault scenarios
├── infra/                  # Docker / Prometheus / Jaeger
├── scripts/                # Developer and demo scripts
├── docs/
│   ├── PROJECT_PLAN.md
│   ├── ARCHITECTURE.md
│   ├── AGENT_DESIGN.md
│   ├── MCP_DESIGN.md
│   ├── RELIABILITY.md
│   ├── LEARNING_ROADMAP.md
│   └── learning/
├── .github/
├── AGENTS.md               # Codex repository instructions
├── CONTRIBUTING.md
├── SECURITY.md
├── Makefile
└── README.md
```

## Roadmap

### v0.1 - Agent MVP

- [x] Spring Boot Order Service
- [x] MySQL and Redis integration
- [x] Redis fault injection
- [ ] LangGraph AgentState
- [ ] evidence collection
- [ ] structured diagnosis
- [ ] remediation planning
- [ ] human approval
- [ ] recovery verification

### v0.2 - MCP tool layer

- [ ] Observability MCP server
- [ ] Operations MCP server
- [ ] MCP client integration
- [ ] typed tool results
- [ ] timeout and error contracts

### v0.3 - Agent backend

- [ ] FastAPI
- [ ] asyncio evidence collection
- [ ] SSE execution stream
- [ ] incident API
- [ ] approval API

### v0.4 - Reliability

- [ ] retry policies
- [ ] replanning
- [ ] checkpoint / resume
- [ ] PostgreSQL persistence
- [ ] idempotency
- [ ] tool risk policy

### v0.5 - Observability

- [ ] OpenTelemetry
- [ ] Prometheus
- [ ] Jaeger
- [ ] structured logging
- [ ] agent execution metrics

### v1.0 - Public release

- [ ] 6+ reproducible scenarios
- [ ] integration tests
- [ ] evaluation report
- [ ] architecture documentation
- [ ] one-command local demo
- [ ] stable release notes

## Target developer flow

The following commands describe the target developer experience. They will be enabled milestone by milestone.

```bash
cp .env.example .env
make dev-up
make smoke-test
make fault SCENARIO=redis-timeout
make incident SCENARIO=redis-timeout
make recover SCENARIO=redis-timeout
```

## Learning-first development

This repository is also a learning project. Core agent concepts are intentionally not delegated blindly to coding agents.

The project owner should personally understand and be able to explain:

- AgentState design;
- LangGraph topology;
- conditional routing;
- MCP boundaries;
- tool schemas and risk levels;
- retry vs replan;
- checkpoint and resume;
- human approval;
- idempotency;
- verification strategy;
- async execution.

Codex is configured through [`AGENTS.md`](./AGENTS.md) to act as a teacher and pair programmer for these areas.

## Contributing

Read [`CONTRIBUTING.md`](./CONTRIBUTING.md) before making changes.

All non-trivial changes should begin with a GitHub Issue and enter `main` through a Pull Request. Direct development on `main` is not allowed.

## Security

This repository is designed for local development and controlled experimentation. Do not point mutating tools at production infrastructure.

Never commit API keys, passwords, private certificates, tokens, or `.env` files.

See [`SECURITY.md`](./SECURITY.md).

## License

MIT
