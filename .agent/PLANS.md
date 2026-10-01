# Codex ExecPlans

Use an ExecPlan for a complex feature, multi-module change, milestone, or task likely to require sustained investigation/implementation.

An ExecPlan is a living implementation artifact. It must be understandable by a Codex session that only has the current checkout plus the plan.

## Required sections

### Title / objective
What concrete capability will exist when this plan is complete?

### Relevant repository context
List only the files/docs/components needed to understand this plan.

### Acceptance criteria
Use observable behavior/tests, not vague “implemented” statements.

### Non-goals
Keep scope bounded.

### Design / approach
Describe the current intended implementation. Update it if evidence changes the plan.

### Work breakdown
Checkboxes or ordered tasks small enough to verify incrementally.

### Progress log
Append dated/ordered concise entries with changes, commands and evidence.

### Decisions / discoveries
Record important surprises and decisions that future work must know.

### Verification
Exact commands/tests/scenarios used to prove completion.

### Remaining risks / follow-ups
Distinguish blockers from future enhancements.

## Lifecycle
- Store current plans in `.agent/exec-plans/active/`.
- Update the plan while working; do not let it become stale.
- When acceptance criteria are verified, move it to `.agent/exec-plans/completed/`.
- One top-level Codex Goal may span multiple ExecPlans.

## Planning discipline
Plan enough to coordinate, then implement. Do not spend the Goal budget writing elaborate plans without tool calls/code changes.
