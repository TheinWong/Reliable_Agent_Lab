# ExecPlan 0007 — Clean-checkout v0.1.0 release audit

## Objective
Verify the entire `CODEX_GOAL.md` completion surface from a committed, clean checkout with fresh Compose state. Fix any final regression and leave public documentation and the release checklist consistent with evidence.

## Relevant repository context
`AGENTS.md`, `CODEX_GOAL.md`, `README.md`, `docs/50-roadmap/{ROADMAP,RELEASE_CRITERIA}.md`, completed ExecPlan 0006, CI workflow, Makefile, scenario/evaluation scripts, and current Git/Compose state.

## Acceptance criteria
- A clean committed checkout with fresh Compose project volumes follows README Quick Start successfully, including smoke, MCP smoke, S1–S4, evaluation, and teardown.
- Python Ruff/mypy/pytest and both Java Maven modules pass on the final commit; Compose configuration is valid.
- All ten `CODEX_GOAL.md` verification items have direct evidence or a documented release blocker; no missing item is inferred from mere code presence.
- CI workflow command coverage and YAML semantics are checked locally; hosted CI status is reported honestly.
- No secrets, debug artifacts, or unsupported production claims are committed; learning docs, ADR, roadmap and release criteria reflect actual behavior.

## Non-goals
Production authentication, real payment charges, non-idempotent external side effects, stretch S5/S6, and a public tag/GitHub Release. Remote synchronization was originally out of scope but was separately authorized by the owner on 2026-10-01.

## Design / approach
Commit the verified S3/S4 scenario slice, then replay the documented commands from a temporary worktree at that commit with a separate Compose project. Preserve existing demo volumes by using a new project name. Inspect output and fix failures in the source branch, then repeat affected checks. Maintain an explicit requirement-by-requirement evidence audit.

## Work breakdown
- [x] commit completed ExecPlan 0006 work on the local feature branch (`0f3f676`)
- [x] fresh worktree/fresh Compose-project README replay
- [x] final test, tracing, HITL, idempotency and CI evidence audit (`VERIFICATION_AUDIT.md`)
- [x] docs/security/secrets and release checklist audit; hosted CI passed after owner-authorized import
- [x] finalize the evidence and documentation audit, close this ExecPlan, and determine Goal status

## Progress log
- 2026-10-01: opened after S1–S4 passed sequentially from a rebuilt stack and `make evaluate` returned 4/4. Clean committed-checkout replay and final audit still pending.
- 2026-10-01: clean worktree at `0f3f676` with fresh Compose volumes passed `make sync lint python-test compose-check` (42 Python tests), `make java-test` (9+4), `make dev-up`, MCP/smoke, all S1–S4, `make evaluate` (4/4), and `make dev-down`. Audited CI YAML and found integration job lacked explicit `uv`; added setup-uv/setup-python/uv sync, locally parsed YAML and checked coverage. Added `VERIFICATION_AUDIT.md`, updated architecture/config/model docs and release boundary. No remote configured; hosted GitHub Actions remains unverified and no release is published.
- 2026-10-01: revalidated the committed CI workflow with official actionlint 1.7.12 (download SHA-256 matched upstream release); exit 0, no diagnostics. Docker Hub image pull failed with an unexpected EOF, so the checksum-verified official release binary was used. Hosted CI remains unavailable without an authorized remote.
- 2026-10-02: the owner authorized replacing the early public repository tree while preserving history. PR #4 imported the exact local tree and was squash-merged as `e08034f`. Branch protection required legacy check names, so the CI jobs were renamed without changing protection. Hosted push and PR runs passed Python, Java, Compose boot, smoke, MCP smoke, S1–S4 and evaluation. The local source repository was connected to the public remote; this final audit branch starts at `origin/main`. Documentation is being updated to replace the earlier hosted-CI blocker with direct evidence.
- 2026-10-02: post-merge `main` run 36967875288 passed all three required jobs. The release evidence, roadmap, changelog, README and evaluation notes now distinguish the verified public code MVP from the unpublished version tag/Release. Final documentation changes are being submitted through the protected-branch PR workflow.

## Decisions / discoveries
Use an isolated temporary Compose project for the fresh replay so existing project volumes and incident evidence remain untouched.

## Verification
See `docs/50-roadmap/VERIFICATION_AUDIT.md` for itemized commands, counts, incident IDs, trace assertions and the hosted-CI limitation.

## Remaining risks / follow-ups
The documentation follow-up PR still needs verification. No `v0.1.0` tag or GitHub Release is authorized or claimed. GitHub Actions reported upstream Node.js 20 deprecation and Ubuntu runner-image migration notices; they did not fail this run and should be revisited during future maintenance.
