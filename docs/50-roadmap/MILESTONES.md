# Milestones

Suggested ExecPlan boundaries. Codex may merge/split if evidence shows a better path, while preserving the Goal.

## M0 Foundation
Exit: repo builds/tests locally; Compose config valid; CI scaffolding exists.

## M1 Faultable backend
Exit: at least three services boot, telemetry works, Redis fault can be injected/reset deterministically.

## M2 Agent API + state
Exit: incident can start a minimal graph; events/state are inspectable with deterministic test doubles.

## M3 Multi-agent investigation
Exit: supervisor delegates at least metrics/logs/trace and receives structured reports; parallel path tested.

## M4 MCP conversion
Exit: investigation capabilities operate through MCP contracts with error/timeout tests.

## M5 Remediation + HITL + verifier
Exit: one scenario reaches approval, resumes, mutates local demo safely, and is independently verified.

## M6 Durability
Exit: checkpoint survives agent-service restart and mutating action is protected from duplicate execution.

## M7 Scenario suite + observability
Exit: four ground-truth scenarios run, traces show handoffs/tool calls, core quality metrics are reported.

## M8 v0.1.0 polish
Exit: `CODEX_GOAL.md` verification surface passes from a clean checkout or every residual exception is explicitly justified as release-blocking.
