# Codex Goal Mode

Codex Goals are thread-scoped persistent objectives. The repository file `CODEX_GOAL.md` is the human-readable contract used to create the active Goal; it does not activate Goals by itself.

## Start pattern
Use `/goal` with a compact completion contract referencing repository evidence. The launch prompt supplied with this pack contains a ready-to-use command.

## Goal discipline
A Goal is not complete because implementation feels done. Completion must be audited against:
- tests;
- scenario outputs;
- build/start commands;
- traces;
- generated artifacts/docs;
- the criteria in `CODEX_GOAL.md`.

## Continuation
When evidence says the current acceptance criteria are not met, choose the next useful action and continue while the Goal remains active and budget/resources allow.

## When to pause/stop
Pause/stop only for a real blocker defined in `CODEX_GOAL.md`, budget limits, user interruption, or completion.

## Goal vs ExecPlan
- Goal = persistent release outcome for the Codex thread.
- ExecPlan = repository artifact describing one large implementation slice and its evolving evidence.
Use both: Goal keeps the finish line; ExecPlans keep implementation navigable.

## Source references
OpenAI Codex Goal documentation:
https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex

Codex ExecPlan guidance:
https://developers.openai.com/cookbook/articles/codex_exec_plans
