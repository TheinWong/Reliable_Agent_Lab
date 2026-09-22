# Contributing to Reliable Agent Lab

Thank you for contributing.

This project uses an Issue-first, Pull-Request-based workflow. The rules are intentionally strict enough to keep the repository understandable while still being practical for a small open-source project.

## 1. Before you start

Read:

- `README.md`
- `AGENTS.md`
- the relevant design document under `docs/`

For non-trivial changes, create or use an existing GitHub Issue before implementation.

Small typo-only documentation fixes may skip the Issue requirement.

## 2. Issue format

A feature or engineering Issue should contain:

```text
Background
Goal
Scope
Non-goals
Acceptance Criteria
Technical Notes
```

Keep scope explicit. If implementation reveals a meaningful scope change, update or discuss the Issue instead of silently expanding the PR.

## 3. Branch strategy

`main` is protected and should always represent an integratable state.

Never develop directly on `main`.

Use:

```text
feat/<issue-id>-<short-description>
fix/<issue-id>-<short-description>
refactor/<issue-id>-<short-description>
docs/<issue-id>-<short-description>
test/<issue-id>-<short-description>
chore/<issue-id>-<short-description>
```

Examples:

```text
feat/12-agent-state
feat/21-observability-mcp
fix/33-sse-disconnect
docs/40-architecture
```

Avoid vague names such as `test`, `new`, `update`, `temp`, or `codex-work`.

## 4. Commit convention

Use Conventional Commits:

```text
<type>(<scope>): <description>
```

Types:

- feat
- fix
- refactor
- test
- docs
- chore
- ci
- perf

Common scopes:

- agent
- api
- mcp
- demo
- infra
- observability
- scenario
- ci
- docs

Examples:

```text
feat(agent): add structured diagnosis model
feat(mcp): expose service health tool
fix(api): handle disconnected SSE client
test(agent): cover verification replan path
docs(readme): document redis fault demo
chore(ci): add java test workflow
```

Commit rules:

- one coherent logical change per commit;
- no secrets or `.env` files;
- no unrelated refactors;
- no meaningless messages such as `update` or `fix`;
- temporary debugging code must not enter `main`.

## 5. Pull requests

PR titles should also follow Conventional Commit style.

Example:

```text
feat(agent): implement diagnosis workflow
```

Each PR should explain:

- Summary
- Why
- Changes
- Architecture Impact
- Testing
- Related Issue

A PR should be small enough to review. Prefer multiple coherent PRs over one very large change.

## 6. Merge policy

Default strategy:

```text
Squash and Merge
```

The PR title becomes the final commit message on `main`.

Do not use merge commits unless repository policy changes explicitly.

Do not rewrite published `main` history.

## 7. Branch protection

Recommended `main` rules:

- Require pull request before merging
- Require required status checks
- Require conversation resolution
- Require linear history
- Disallow force pushes
- Disallow deletion

For a single-maintainer phase, a second-person review is not mandatory. If more maintainers join, enable at least one approving review and consider `CODEOWNERS`.

## 8. Testing expectations

### Python

```bash
ruff check .
ruff format --check .
pytest
mypy .
```

Run the narrowest relevant tests first, then the broader affected checks.

### Java

```bash
mvn test
```

### Infrastructure

```bash
docker compose -f infra/docker-compose.yml config
```

As the project grows, scenario smoke tests will become required checks.

## 9. Documentation expectations

Update docs in the same PR when behavior changes.

- architecture changes -> `docs/ARCHITECTURE.md`
- agent graph changes -> `docs/AGENT_DESIGN.md`
- MCP boundary changes -> `docs/MCP_DESIGN.md`
- reliability policy changes -> `docs/RELIABILITY.md`
- developer command changes -> `README.md` and this file

Do not document features as implemented before they are tested and available.

## 10. Security

Never commit:

- API keys
- database passwords
- GitHub tokens
- private certificates
- `.env`
- production credentials

Mutating tools must target only the local demo environment unless a future design explicitly adds a safe external environment.

## 11. Definition of done

Before requesting review:

- [ ] Issue acceptance criteria are satisfied
- [ ] tests cover new behavior
- [ ] relevant tests pass
- [ ] lint and type checks pass
- [ ] docs are updated
- [ ] no secrets are present
- [ ] no unrelated changes are included
- [ ] limitations are documented
- [ ] the PR links its Issue
