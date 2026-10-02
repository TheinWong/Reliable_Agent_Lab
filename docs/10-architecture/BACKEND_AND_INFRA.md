# Backend and Infrastructure

## Python Agent API
Target responsibilities:
- create incident;
- get incident state;
- stream execution events via SSE;
- approve/reject suspended action;
- expose health/readiness;
- correlate request/run/incident ids.

Recommended endpoints (may evolve):
- `POST /api/incidents`
- `GET /api/incidents/{id}`
- `GET /api/incidents/{id}/events`
- `POST /api/incidents/{id}/approval` with the plan's `action_id` and an `approved` boolean

## Async behavior
Use async for independent I/O. Evidence calls may execute concurrently. Do not hold one HTTP request open for the entire incident lifecycle except the explicit event stream.

## Durable state
The current S1 flow uses PostgreSQL for both LangGraph checkpoints and separate incident/event API records. `agent-api` resumes a persisted approval-paused thread after restart. Redis remains the Java order cache, not the workflow's durable store.

## Demo services
Use Java 21 + Spring Boot. Keep domain logic small but real enough to exercise:
- HTTP calls between services;
- MySQL access;
- Redis cache/access;
- health/metrics;
- structured logs;
- trace propagation;
- deterministic fault injection.

## Docker Compose
Target a clean local boot. Use healthchecks and deterministic ports. Avoid requiring host-specific software beyond Docker, Git and documented build tooling.
