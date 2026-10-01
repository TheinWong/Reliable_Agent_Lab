# v0.1.0 local verification audit — 2026-10-01

This audits `CODEX_GOAL.md` against commit `0f3f676` in a separate clean worktree (`git status --short` empty) and a fresh Compose project with new database volumes. The subsequent CI/documentation-only patch is checked separately. This is local MVP evidence, not a claim that a GitHub release or hosted workflow has run.

| Goal verification item | Current evidence | Result |
| --- | --- | --- |
| 1. Clean stack boot | `cp .env.example .env`; `make dev-up` from the clean worktree; all 12 Compose services healthy | Pass |
| 2. Smoke | `make smoke-test`, incident `4c48cd4c` | Pass |
| 3. Python quality | `make sync lint python-test compose-check`; Ruff, mypy, 42 pytest cases passed | Pass |
| 4. Java quality | `make java-test`; order-service 9/9 and downstream-service 4/4 passed | Pass |
| 5. Four ground-truth scenarios | S1–S4 scripts passed sequentially from new volumes; `make evaluate` checked latest persisted incidents against fixture diagnosis/action/target, reports and recovery: 4/4 | Pass |
| 6. Runtime delegation/tool traces | Each scenario's `verify_traces.py` asserted Supervisor, Metrics/Logs/Trace, tool and Java reset spans with parentage; S3/S4 also asserted real post-injection downstream spans in the order-preview trace | Pass |
| 7. HITL restart/resume | Each script observed `awaiting_approval`, restarted `agent-api`, read the same persisted incident, approved and reached resolved verification | Pass |
| 8. Repeated mutation safety | Each script sent the same approval again, asserted one PostgreSQL action row and one Java reset span in the resumed trace; reset endpoints are idempotent | Pass for named local-demo resets; not general exactly-once semantics |
| 9. README Quick Start | The documented sequence from `.env` copy through `make dev-down` passed in the clean worktree | Pass |
| 10. Accurate roadmap/checklists | Roadmap, ADR-012, scenario catalog, MCP boundaries, walkthroughs and README inspected/updated for S1–S4 and limitations | Pass for local feature scope |

Clean-worktree scenario incident IDs: S1 `824983da-9c8e-4b50-a6c7-d545ff0a7891`, S2 `e5b81c29-cbd9-4080-909c-32bfe295a912`, S3 `bee63fd7-7f21-42fa-a7a6-93cf16782203`, S4 `46dacc31-0b5c-4a35-9f81-afaf98ef2dab`. Jaeger returned separate investigation/resume trace IDs plus real downstream IDs for S3/S4. Jaeger storage is ephemeral, so command output is the durable evidence summary after teardown.

## CI and release boundary

`.github/workflows/ci.yml` defines Python, both Java modules, Compose boot, MCP/smoke, S1–S4, and evaluation jobs. Its YAML parsed locally, and the integration job now installs `uv` and Python before invoking scenario scripts. The corresponding commands passed locally in a clean worktree. A separate local static check with the official actionlint 1.7.12 binary (verified SHA-256 `aba9ced2dee8d27fecca3dc7feb1a7f9a52caefa1eb46f3271ea66b6e0e6953f`) returned exit 0 with no diagnostics. No Git remote is configured; hosted GitHub Actions has not run, and this audit does **not** call its checks green. No remote push, repository setup, tag, or release was performed. Before publishing a public v0.1.0 release, connect a remote with the owner's authorization and confirm hosted CI as required by `RELEASE_CRITERIA.md`.

## Known scope limits

S2 is an application-boundary controlled MySQL read failure, not a physical database outage or pool exhaustion. S4 is a stateless payment preview, not a charge. The API is loopback-bound for local demo and has no production authentication. Jaeger storage is ephemeral. The graph has bounded retry and explicit unresolved termination but no semantic replan; no live-model adapter/test is claimed. Action safety is specific to these idempotent reset endpoints, not arbitrary exactly-once external effects.
