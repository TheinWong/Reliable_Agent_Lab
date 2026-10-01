# Context Loading Strategy

The repository intentionally avoids one giant instruction document.

## Always available
Codex receives `AGENTS.md` automatically when working in the repo.

## At project start / Goal creation
Read:
- `CODEX_GOAL.md`
- `docs/INDEX.md`
- `docs/00-product/*`
- `docs/50-roadmap/ROADMAP.md`
- `.agent/PLANS.md`

Then read architecture docs needed for the first ExecPlan.

## Per-task reading
Examples:

### Agent topology/state work
Read:
- `MULTI_AGENT_DESIGN.md`
- `STATE_AND_HANDOFFS.md`
- `RELIABILITY_AND_SAFETY.md`

### MCP tool work
Read:
- `MCP_AND_TOOL_BOUNDARIES.md`
- `TESTING_STRATEGY.md`
- `RELIABILITY_AND_SAFETY.md`

### FastAPI/backend work
Read:
- `BACKEND_AND_INFRA.md`
- `CODING_STANDARDS.md`
- `CONFIG_AND_SECRETS.md`

### Scenario work
Read:
- `SCENARIO_SPEC.md`
- `SCENARIO_CATALOG.md`
- relevant architecture/tool docs.

### GitHub/release work
Read only the `60-github/` docs plus release criteria.

## Rule
Do not repeatedly load unrelated documents just because they exist. Keep docs small and cross-linked so current context stays focused.
