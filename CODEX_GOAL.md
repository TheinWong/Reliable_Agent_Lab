# Codex Goal Contract — v0.1.0 Public MVP

This file is a repository-side reference for the thread-scoped Codex Goal. It does not itself activate Goal mode.

## Desired end state
Deliver a runnable open-source v0.1.0 MVP of Reliable Agent Lab that demonstrates a real multi-agent tool-using workflow over a reproducible Java microservice environment.

The MVP must include:
- a LangGraph supervisor coordinating at least Metrics, Logs and Trace specialist agents;
- a distinct Remediation Agent and independent Verifier Agent;
- structured shared state and structured specialist reports;
- at least three MCP capability groups covering investigation and operations;
- a FastAPI incident API with an event stream and an approval endpoint;
- parallel evidence collection where independent;
- explicit timeout/retry behavior;
- at least one human-in-the-loop mutating action;
- checkpoint/resume for an interrupted incident workflow;
- idempotency protection for mutating operations;
- OpenTelemetry traces that show agent delegation and tool calls;
- a Spring Boot multi-service demo environment using MySQL and Redis;
- at least four deterministic fault scenarios with ground truth;
- automated tests and CI;
- a public-facing README with a reproducible local quick start;
- architecture, design-decision and reverse-learning documentation.

## Verification surface
The Goal is complete only when evidence demonstrates all of the following:

1. `docker compose up -d --build` (or the documented equivalent) starts the local stack from a clean checkout.
2. The documented smoke test succeeds.
3. Python lint/type/test commands are green.
4. Java build/tests are green.
5. At least four scenario tests can inject a fault, create an incident, observe multi-agent investigation, execute or approve remediation, and verify recovery or a clearly documented expected non-recovery.
6. The runtime trace shows supervisor delegation plus specialist/tool spans.
7. At least one workflow can pause for approval and resume from persisted state after an agent-service restart.
8. A repeated mutating request does not create duplicate side effects.
9. README instructions are tested against the actual repository.
10. Roadmap/checklists accurately distinguish completed, partial and future functionality.

## Constraints
- Preserve the architecture and boundaries described by repository docs unless a contradiction or blocker is documented.
- Do not introduce a second primary agent framework.
- Do not require Kubernetes or local LLM hosting for v0.1.0.
- Do not add RAG, long-term memory, or fine-tuning merely to expand scope.
- Do not claim unsupported production guarantees.
- Keep the demo services intentionally small.
- Prefer deterministic local dependencies and test doubles where external credentials are unavailable.
- Never commit secrets.

## Iteration policy
After each material implementation step:
1. run the narrowest relevant checks;
2. inspect failures and evidence;
3. update the active ExecPlan;
4. choose the next action that removes the largest blocker to the v0.1.0 acceptance criteria;
5. periodically run the integrated smoke/scenario suite.

Do not stop merely because one milestone is complete while Goal acceptance criteria remain unmet.

## Blocked stop condition
Stop substantive work and report clearly if no defensible local path remains because of:
- missing mandatory credentials with no local/test substitute;
- unavailable platform capability that the acceptance criteria fundamentally depend on;
- irreconcilable toolchain/environment incompatibility;
- a required destructive remote operation not authorized by the user.

The blocker report must contain:
- completed work;
- failing acceptance criteria;
- evidence/commands;
- attempted alternatives;
- minimum user input required to continue.
