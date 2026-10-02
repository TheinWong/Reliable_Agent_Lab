# GitHub Repository Setup

This document describes recommended settings once the local project is connected to a GitHub repository.

## Repository
Recommended name: `reliable-agent-lab`.
Visibility: public only when the owner is ready; Codex must not change visibility without explicit approval.
Default branch: `main`.

## Branch protection / ruleset
Recommended for `main`:
- require pull request before merge;
- require CI checks;
- require conversation resolution;
- require linear history;
- block force pushes;
- block branch deletion.

For a single maintainer, do not require a second approving reviewer unless desired.

## Merge policy
Recommended: Squash and Merge.
Disable merge commits if the owner wants a clean linear history.

## Labels
Suggested labels:
- `type:feature`, `type:bug`, `type:docs`, `type:test`, `type:refactor`, `type:chore`
- `area:agent`, `area:mcp`, `area:api`, `area:demo-service`, `area:infra`, `area:observability`, `area:scenario`
- `priority:p0`, `priority:p1`, `priority:p2`
- `good-first-issue`, `help-wanted`

## Milestones
Suggested:
- `v0.1-foundation`
- `v0.1-multi-agent`
- `v0.1-reliability`
- `v0.1-release`

## GitHub Project board (optional)
Columns/statuses:
- Backlog
- Ready
- In Progress
- Review
- Done

## Remote-operation policy
Codex may prepare local changes regardless of GitHub connectivity. Creating issues/PRs, pushing branches, configuring rulesets, adding secrets or publishing releases requires the current Codex thread to have explicit user authorization and the required authentication.
