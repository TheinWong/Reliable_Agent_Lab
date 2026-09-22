# Reliability Design

## Goal

A production-oriented agent should remain understandable and safe when tools, networks, model outputs, or processes fail.

## Retry

Retry only failures likely to succeed without changing the plan.

Examples:

- network timeout;
- temporary MCP server unavailable;
- transient rate limit.

Retry policy should be bounded by:

- maximum attempts;
- timeout;
- backoff;
- overall run budget.

## Replan

Replan when the chosen action was semantically ineffective or new evidence changes the diagnosis.

Examples:

- remediation executes but verification fails;
- tool result contradicts the plan;
- expected dependency is healthy, invalidating the previous hypothesis.

## Checkpoint and resume

Important goals:

- pause before human approval;
- survive process restart;
- resume the same logical run;
- avoid replaying completed mutating actions.

The human maintainer should be able to explain exactly what state is persisted and how the run is identified.

## Human approval

Approval policy should be deterministic and code-visible.

Suggested categories:

- read-only: automatic;
- low-risk reversible mutation: configurable;
- high-risk or broad-impact mutation: approval required.

## Idempotency

Mutating tools must address duplicate execution.

Potential mechanisms:

- action_id;
- idempotency_key;
- execution record;
- state check before mutation.

The exact mechanism may vary by tool.

## Verification

Verification must independently query the environment after remediation.

Example criteria may include:

- health is UP;
- error rate falls below threshold;
- latency returns below threshold;
- dependency status is healthy;
- a smoke request succeeds.

## Bounded execution

Every run should have limits such as:

- max graph steps;
- max replans;
- max retries per tool;
- wall-clock timeout;
- model/tool budget where appropriate.

## Observability

Correlate:

- incident_id;
- run_id;
- graph node;
- LLM call;
- tool call;
- retry/replan;
- approval;
- verification.

Reliability failures should be visible, not silently recovered without trace.
