# Architecture

## Design intent

The system separates four concerns:

1. agent orchestration;
2. API/service delivery;
3. external tool integration;
4. the fault-injectable business environment.

This separation is intentional. The agent should reason over stable tool contracts rather than knowing how Prometheus, Redis, or Spring Boot are implemented.

## Components

### Agent runtime

Responsibilities:

- maintain AgentState;
- execute the LangGraph topology;
- call tools through an abstract tool layer;
- apply risk/retry/replan policies;
- pause and resume execution;
- produce structured events for the API layer.

### FastAPI service

Responsibilities:

- create incidents/runs;
- expose run state;
- stream execution events;
- receive approvals;
- map domain errors to HTTP responses.

It does not own reasoning logic.

### MCP servers

Initial groups:

- observability: health, logs, metrics;
- database: read-only database inspection when needed;
- operations: bounded mutating actions against the local demo environment.

MCP creates a replaceable integration boundary. For example, a future logs backend could change from files to Loki without changing agent reasoning code.

### Demo service

The Spring Boot Order Service exists to provide:

- real API behavior;
- real MySQL/Redis dependencies;
- realistic health and metrics;
- deterministic faults;
- a Java service integration target.

It must stay intentionally small.

## Detection vs diagnosis

The LLM is not responsible for primary anomaly detection in V1.

Deterministic monitoring rules or scenario scripts create Incidents. This keeps the boundary clear:

```text
monitoring/scenario -> Incident -> Agent investigation
```

The agent is evaluated on investigation and recovery, not on guessing whether a system is abnormal.

## Data and control flow

```text
Incident
  |
  v
Agent API
  |
  v
LangGraph runtime
  |
  +--> MCP observability tools --> service/metrics/logs
  |
  +--> LLM for diagnosis and plan
  |
  +--> risk policy
  |
  +--> human approval when required
  |
  +--> MCP operation tool
  |
  +--> MCP observability tools again
  |
  v
Verification result
```

## Persistence evolution

V1 may use in-memory or SQLite checkpoints for learning.

A later milestone moves durable execution to PostgreSQL so process restart and approval resume can be demonstrated explicitly.

Redis is used by the demo service and may later be used for cache/session concerns, but it should not become an unnecessary shared dependency.

## Deployment model

Local:

- Agent API/runtime
- MCP servers
- Spring Boot service
- MySQL
- Redis
- Prometheus
- Jaeger
- optional PostgreSQL

Remote:

- LLM API
- GitHub repository / Actions

The project intentionally avoids local LLM hosting in V1.
