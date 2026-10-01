# GitHub Workflow

## Branch strategy
Never develop directly on `main`.
Use branches such as:
- `feat/<issue-or-plan>-short-name`
- `fix/<issue-or-plan>-short-name`
- `docs/<issue-or-plan>-short-name`
- `chore/<issue-or-plan>-short-name`

For Codex autonomous local implementation, one branch per ExecPlan is acceptable when the plan remains reviewable.

## Commits
Use Conventional Commits:
- `feat(agent): add supervisor fan-out`
- `feat(mcp): add metrics server`
- `fix(runtime): make operation idempotent`
- `test(scenario): add redis timeout regression`
- `docs(architecture): record verifier isolation`

Keep commits coherent. Avoid giant “implement everything” commits even if Codex is doing the implementation.

## Pull requests
A PR should include:
- summary and motivation;
- linked Issue/ExecPlan/milestone;
- architecture impact;
- test evidence;
- screenshots/trace evidence when useful;
- known limitations.

Prefer Squash and Merge for public history unless the maintainer chooses otherwise.

## Main protection (recommended when GitHub repo exists)
- PR required;
- required CI status checks;
- conversations resolved;
- linear history;
- force pushes/deletion disabled.

For a single-maintainer project, do not require a second approving reviewer unless desired.

## Codex remote actions
Codex can freely manage local branches/commits.
Remote push, PR creation or GitHub issue changes should happen only when the current user prompt/Goal explicitly authorizes remote operations and authentication is available.
Never change repository visibility, protections or secrets without explicit approval.
