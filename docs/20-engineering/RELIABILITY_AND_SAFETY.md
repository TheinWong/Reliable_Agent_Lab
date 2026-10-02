# Reliability and Safety

## Retry vs replan
Retry is for likely transient execution failures, such as bounded transport timeouts or temporary dependency errors.
Replan is for semantic failure: the action was wrong/insufficient, verification failed, or new evidence invalidates the current plan.
Do not turn all failures into retries.

## Bounded execution
Every workflow should have limits such as max steps/replans, tool timeout, and optional token/time budget.

## Human approval
At least one real mutating scenario must pause for approval. The pause must be resumable rather than simulated by a synchronous confirmation prompt.

## Idempotency
Every mutating action should have an action identity/idempotency key or equivalent state that prevents unsafe duplicate effects after retry/resume.

## Verification
Verifier re-collects fresh evidence and evaluates explicit recovery criteria. A successful operation response is insufficient.

## Permission model
- investigation agents: read-only tools;
- remediation agent: plan generation, not unrestricted execution;
- operations: constrained server-side implementation;
- supervisor: orchestration, not blanket tool permissions.

## Fail-safe behavior
When diagnosis confidence/evidence is insufficient for a risky action, prefer approval/escalation or explicit unresolved status over guessing.
