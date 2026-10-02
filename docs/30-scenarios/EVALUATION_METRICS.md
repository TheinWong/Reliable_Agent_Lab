# Evaluation Metrics

Evaluation is supporting evidence for engineering quality, not the project's primary identity.

## Core outcome metrics
- root-cause correctness against scenario ground truth;
- affected-service correctness;
- remediation compatibility with allowed ground-truth actions;
- resolution success rate;
- verification correctness.

## Multi-agent metrics
- delegation accuracy: did Supervisor invoke relevant specialists without obviously unnecessary ones?
- parallel investigation wall-clock time;
- specialist report usefulness/completeness;
- evidence conflict rate and conflict handling outcome.

## Efficiency metrics
- end-to-end incident duration;
- agent/model/tool call counts;
- retry/replan counts;
- token usage/cost when available.

## Reliability metrics
- tool timeout recovery;
- restart/resume success;
- duplicate-side-effect prevention;
- HITL pause/resume success.

## Reporting
Do not present tiny scenario suites as statistically general production benchmarks. Report exact scenario counts and limitations.

The executable v0.1 regression summary is `make evaluate`. It reads the latest PostgreSQL incident per S1–S4 fixture and checks completion, fixture-matched diagnosis/action/target, three completed specialist reports, approval, one completed execution result, independent recovery, and scenario-specific evidence. The four scenario scripts separately assert live HTTP symptoms, agent restart/resume, one persisted action row after repeated approval, and Jaeger spans/parentage. The evaluator is intentionally descriptive: a 4/4 result means those four controlled cases passed, not measured production root-cause accuracy.

Local replay on 2026-10-01 after `make dev-down` and `make dev-up`: smoke and S1–S4 passed sequentially; `make evaluate` returned 4/4 for incidents `2c6dee87`, `37cded4c`, `a350d0bb`, and `62d24915` (IDs abbreviated). A separate clean worktree at commit `0f3f676` with fresh Compose project volumes then passed `make sync lint python-test compose-check` (42 Python tests), `make java-test` (9 order-service and 4 downstream-service tests), `make dev-up`, MCP smoke, smoke, S1–S4 sequentially, and `make evaluate` 4/4 (incident IDs `824983da`, `e5b81c29`, `bee63fd7`, `46dacc31`). The four-case result is a deterministic regression check, not a production accuracy estimate. The [hosted PR run](https://github.com/TheinWong/Reliable_Agent_Lab/actions/runs/36875820249) subsequently passed the same four scenario steps and evaluation.
