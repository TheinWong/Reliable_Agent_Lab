# Codex Operating Model

## Intent
Codex is expected to implement the project with high autonomy. The human owner prioritizes speed and will reverse-study the finished repository later.

## Work style
- Use the active Codex Goal as the durable end state.
- Break implementation into ExecPlans/milestones.
- Continue from evidence rather than waiting for micro-approval.
- Make normal engineering decisions autonomously when consistent with docs.
- Prefer working code and verification over long speculative plans.

## What Codex may decide autonomously
Examples:
- module/file organization within documented boundaries;
- specific maintained libraries or drivers;
- local dev ports if conflict-free and documented;
- DTO/internal naming;
- test fixture organization;
- implementation details of typed models;
- CI job decomposition;
- mock/fake strategy for credential-free tests.

## What requires user input
Only material boundary changes, credentials with no fallback, destructive remote operations, or irreducible blockers.

## Repository hygiene
As implementation progresses, Codex must also maintain the reverse-learning artifacts in `docs/90-learning/` so the owner can later ask the codebase questions efficiently.

## Avoid
- stopping after every small step;
- narrating future work instead of doing it;
- generating the whole system without tests;
- hiding missing features behind TODO-heavy scaffolds;
- claiming live integration when only mocks exist.
