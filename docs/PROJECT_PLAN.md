# Project Plan

## 1. Goal

Build a public, reproducible project that demonstrates production-oriented Agent Engineering rather than prompt-only AI application development.

The project must complement existing experience in memory/context engineering, RAG/retrieval, evaluation, and Java backend development by adding strong evidence for:

- LangGraph orchestration;
- MCP;
- Tool Calling;
- Python/FastAPI backend development;
- async execution and streaming;
- durable execution;
- reliability and safety policies;
- observability;
- end-to-end integration.

## 2. Validation object

The agent acts on a small Spring Boot Order Service backed by MySQL and Redis.

Anomaly detection itself is deterministic. Monitoring rules or scenario scripts create an Incident. The agent starts after the Incident exists.

The agent owns:

1. evidence collection;
2. diagnosis;
3. remediation planning;
4. risk classification;
5. optional human approval;
6. tool execution;
7. independent verification;
8. replan when verification fails.

## 3. Milestones

### Milestone 0 - Repository bootstrap

Deliverables:

- README
- AGENTS.md
- CONTRIBUTING.md
- SECURITY.md
- issue templates
- PR template
- base CI
- branch protection configuration in GitHub

Human learning goal: understand repository workflow and project boundaries.

### Milestone 1 - Faultable Spring Boot service

Implement:

- Order API;
- MySQL persistence;
- Redis cache;
- Actuator health/metrics;
- deterministic Redis fault injection;
- Docker Compose environment.

Acceptance:

- healthy state is reproducible;
- Redis fault creates a visible symptom;
- logs/health/metrics expose enough evidence;
- recovery returns the service to healthy state.

Human-owned design:

- service boundaries;
- Redis use case;
- fault model;
- ground truth.

Codex may assist heavily with DTOs, CRUD, Maven configuration, tests, and Docker.

### Milestone 2 - LangGraph Agent MVP

Start without MCP.

Implement local Python tools:

- query_health();
- query_logs();
- query_metrics();
- recover_fault().

Graph:

```text
START -> collect -> diagnose -> plan -> risk_check
      -> approve/execute -> verify -> END/replan
```

Acceptance:

- Redis incident can complete the full loop;
- diagnosis and plan are structured outputs;
- high-risk execution can pause for approval;
- verification determines whether the run is complete.

Human-owned learning:

- AgentState;
- node responsibility;
- routing;
- state mutation;
- structured output;
- verification semantics.

### Milestone 3 - MCP tool layer

Replace direct tool integration with MCP boundaries.

Initial servers:

- observability;
- operations.

Acceptance:

- graph depends on tool contracts rather than service implementation;
- read and mutating tools are separately classified;
- failures return typed error information;
- at least one transport is documented and tested.

Human-owned learning:

- MCP client/server roles;
- tool schemas;
- protocol boundary;
- timeout and error semantics.

### Milestone 4 - FastAPI agent backend

Implement:

- POST /api/incidents
- GET /api/incidents/{id}
- GET /api/incidents/{id}/events
- POST /api/incidents/{id}/approve
- SSE execution stream
- async evidence collection

Acceptance:

- API can start a run;
- clients can observe progress;
- approval can resume a paused run;
- independent IO-bound evidence tools run concurrently.

Human-owned learning:

- async/await;
- asyncio.gather;
- SSE;
- API boundary design.

### Milestone 5 - Reliability

Implement:

- retry policy;
- replan policy;
- bounded execution;
- checkpoint/resume;
- idempotency;
- explicit action IDs;
- risk policy;
- process restart recovery.

Acceptance:

- transient tool failures retry within limits;
- semantic remediation failure replans;
- a run can resume after restart;
- duplicate side effects are prevented;
- approval survives the expected persistence model.

### Milestone 6 - Observability

Implement:

- structured logs;
- Prometheus metrics;
- OpenTelemetry tracing;
- Jaeger local UI;
- run_id / incident_id correlation.

Trace at least:

- agent run;
- LLM call;
- tool call;
- diagnosis;
- approval;
- action;
- verification.

### Milestone 7 - Scenario suite and evaluation

Add at least:

- Redis timeout;
- MySQL failure;
- slow request;
- HTTP 500;
- downstream timeout;
- connection pool exhaustion.

Metrics:

- diagnosis accuracy;
- resolution success rate;
- tool selection accuracy;
- average tool calls;
- retries;
- end-to-end latency;
- token usage when available.

Evaluation supports regression prevention; it is not the product identity.

### Milestone 8 - Open-source release

Target `v1.0.0`:

- one-command local demo;
- 6+ deterministic scenarios;
- CI green;
- architecture docs current;
- demo screenshot/GIF;
- release notes;
- stable contribution workflow.

## 4. Estimated effort

A realistic target is:

- core V1: roughly 35-50 focused hours;
- reliability + observability + open-source polish: roughly 55-80 total focused hours.

Treat these as planning ranges, not deadlines.

## 5. Learning strategy

Learn in project order, not by finishing entire technologies in isolation:

```text
Python backend basics
-> faultable microservice
-> LangGraph loop
-> MCP
-> reliability / HITL
-> observability / evaluation
```

For core concepts use Codex Teaching Mode. For boilerplate, use Codex Implementation Mode.
