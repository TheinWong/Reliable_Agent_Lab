# Scope and Non-Goals

## v0.1 scope
- supervisor + specialist multi-agent topology;
- metrics/logs/trace investigation;
- remediation planning;
- independent verification;
- MCP-based tools;
- FastAPI incident service;
- Spring Boot demo microservices;
- MySQL and Redis;
- Docker Compose;
- deterministic fault injection;
- HITL, retry, replan, checkpoint/resume, idempotency;
- OpenTelemetry + Jaeger/Prometheus;
- scenario regression tests.

## Non-goals for v0.1
- generic enterprise SRE platform;
- Kubernetes-first deployment;
- production SLA or HA claims;
- long-term agent memory;
- RAG/runbook retrieval as a core subsystem;
- user-facing chat UI;
- autonomous shell access;
- arbitrary infrastructure mutation;
- local large-model hosting;
- model training/fine-tuning;
- more agent roles merely to increase agent count.

## Scope control rule
If a feature does not directly help one of the v0.1 acceptance criteria, defer it unless it removes a concrete blocker.
