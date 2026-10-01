# ExecPlan 0006 — Multi-service fault scenarios S2–S4

## Objective
Add small inventory and payment Spring Boot services, an observable order-service HTTP path through them, and deterministic S2 MySQL, S3 inventory-latency, and S4 payment-5xx scenarios. Extend the existing agent/policy/operations/verification flow only as required to produce honest ground-truth diagnoses and safe recovery/non-recovery outcomes. Keep S1 green.

## Relevant repository context
`AGENTS.md`, `CODEX_GOAL.md`, `.agent/PLANS.md`; `docs/30-scenarios/{SCENARIO_SPEC,SCENARIO_CATALOG,EVALUATION_METRICS}.md`, `docs/10-architecture/{BACKEND_AND_INFRA,MULTI_AGENT_DESIGN,MCP_AND_TOOL_BOUNDARIES}.md`, `docs/20-engineering/{TESTING_STRATEGY,RELIABILITY_AND_SAFETY}.md`; existing Java order service, Compose, MCP contracts, graph, scenario scripts, and CI.

## Acceptance criteria
- Compose boots order, inventory, and payment services with health checks, bounded fault injection/reset endpoints, and a real order request path that calls downstream services.
- S2, S3, and S4 each define machine-readable ground truth and deterministically inject/observe a fault, create an incident, receive structured parallel specialist reports, and resolve through an approval-gated allowed action or explicitly verified expected non-recovery.
- Trace evidence for S3/S4 shows real downstream latency/error topology, not synthetic spans; Metrics/Logs/Trace specialists remain read-only and remediation/verification remain separate.
- Scenario scripts clean up their own faults, are repeatable, and pass together with S1 from a running Compose stack. Python and Java tests, lint/type checks, and CI commands stay green.
- Roadmap, ADR, README, walkthrough and notebook distinguish verified scope from remaining limitations.

## Non-goals
Production credentials/authentication, Kubernetes, unrestricted operations, paid LLM dependency, persistent Jaeger storage, or stretch S5/S6.

## Design / approach
First inspect current Java service and scenario contracts. Implement the minimum real inter-service path and controlled fault APIs before adapting Agent inference. Use typed scenario-specific evidence rather than string matching alone. Keep MySQL authoritative and maintain fail-closed approval for every mutation. If S2's DB fault prevents application-level verification, record expected non-recovery explicitly instead of treating a container health result as success. Add one scenario at a time with runtime evidence.

## Work breakdown
- [x] inspect S2–S4 evidence and Java/Agent extension points; define concrete fault/evidence boundaries
- [x] implement inventory/payment services and order-service downstream path with tests and telemetry
- [x] implement S2 controlled read fault and honest diagnosis/remediation/verification
- [x] implement S3 fault and trace-supported diagnosis/remediation/verification
- [x] implement S4 fault and trace-supported diagnosis/remediation/verification
- [x] run full four-scenario suite and update CI/docs/evaluation surface

## Progress log
- 2026-10-01: opened after ExecPlan 0005 commit `94f6c80`. Current integrated S1 passed 30 Python tests, 5 Java tests, Compose, MCP smoke, smoke, and S1; Jaeger verified agent/tool and Java reset parent spans. Goal verification item 5 (four scenarios) and multi-service target remain open.
- 2026-10-01: added S2's local-only controlled MySQL read fault to order-service: explicit 503, structured event, metrics, idempotent injection/reset endpoints. `make java-test` passed 6 tests; live fault probe returned 503 with `DEMO_MYSQL_UNAVAILABLE` and a counter increment. A subsequent S1 run exposed a trace-export timing race in `verify_traces.py`: Java reset span arrived after Python/Java read spans. Changed verification to poll until that cross-service span arrives; S1 then passed. S2 Agent/MCP diagnosis, operation and scenario script are not yet implemented.
- 2026-10-01: S2 Agent/MCP flow and machine-readable fixture implemented. `make lint python-test` passed 34 tests; `make dev-up`, `make mcp-smoke`, `make scenario SCENARIO=mysql-unavailable`, `make smoke-test`, and S1 regression passed. S2 restarts API at approval, resolves through distinct MySQL reset/probe, checks one PostgreSQL action row and DB-to-cache recovery, and verifies real Java reset parentage in Jaeger. S2 fault is explicitly a controlled application read failure, not actual pool exhaustion or network outage.
- 2026-10-01: inventory/payment containers, real checkout-preview HTTP path, bounded faults, MCP tools/probes, and three-source post-injection evidence implemented. `make test` passed 9 order-service Java tests, 4 downstream Java tests and 41 Python tests; a later evaluator regression brought Python to 42 passing tests. `make lint` and `make compose-check` passed. After `make dev-down`/`make dev-up`, `make mcp-smoke`, `make smoke-test`, and all S1–S4 scenario scripts passed sequentially. Each scenario observed a paused approval across agent-api restart, duplicate-safe approval, independent recovery, and Java reset span parentage; S3/S4 also verified real downstream failure spans linked to checkout-preview traces. `make evaluate` reported 4/4 latest persisted incidents against ground-truth fixtures. CI now runs both Java modules and all four scenarios plus evaluator.

## Decisions / discoveries
S3/S4 require actual HTTP service calls and Java trace propagation, not only separately named services. New fault tools must remain bounded to local demo conditions.
Jaeger OTLP exporters are asynchronous; a missing span immediately after workflow completion is not proof of absence. Integrated trace verification now waits for all required span families within a 20-second bound.

## Verification
Verified commands: `make lint python-test` (42 passed; Ruff and mypy clean), `make test` (41 Python, 9 order Java, 4 downstream Java before final evaluator test), `make compose-check`, `make dev-down`, `make dev-up`, `make mcp-smoke`, `make smoke-test`, each `make scenario SCENARIO=redis-unavailable|mysql-unavailable|inventory-latency|payment-5xx` sequentially, and `make evaluate` (4/4). Scripts queried Jaeger and asserted downstream/operation span topology. CI workflow syntax and command coverage inspected locally; hosted GitHub Actions execution is not claimed.

## Remaining risks / follow-ups
Final v0.1.0 clean-checkout replay, repository/security/doc audit, and release checklist remain in ExecPlan 0007. Hosted GitHub Actions execution cannot be claimed without a remote run; local CI-equivalent commands passed.
