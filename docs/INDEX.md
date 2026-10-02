# Documentation Index

`AGENTS.md` is intentionally short. This directory is the system of record.
Codex should read only the documents relevant to the active task.

## Product and scope
- `00-product/PROJECT_BRIEF.md` — who this project is for and what it demonstrates.
- `00-product/SUCCESS_CRITERIA.md` — project-level success definition.
- `00-product/SCOPE_AND_NON_GOALS.md` — hard scope boundaries.

## Architecture
- `10-architecture/SYSTEM_ARCHITECTURE.md` — components and runtime flow.
- `10-architecture/MULTI_AGENT_DESIGN.md` — agent roles, delegation, context isolation and concurrency.
- `10-architecture/STATE_AND_HANDOFFS.md` — state ownership and contracts between agents.
- `10-architecture/MCP_AND_TOOL_BOUNDARIES.md` — tool servers, permissions and error contracts.
- `10-architecture/BACKEND_AND_INFRA.md` — FastAPI, Java services, storage and observability.
- `10-architecture/DECISION_LOG.md` — architecture decision records.

## Engineering
- `20-engineering/CODING_STANDARDS.md`
- `20-engineering/TESTING_STRATEGY.md`
- `20-engineering/RELIABILITY_AND_SAFETY.md`
- `20-engineering/OBSERVABILITY.md`
- `20-engineering/CONFIG_AND_SECRETS.md`
- `20-engineering/DEPENDENCY_POLICY.md`
- `20-engineering/API_CONVENTIONS.md`
- `20-engineering/PROMPT_AND_MODEL_POLICY.md`

## Scenario system
- `30-scenarios/SCENARIO_SPEC.md` — format for deterministic fault scenarios.
- `30-scenarios/SCENARIO_CATALOG.md` — planned v0.1 scenarios and ground truth.
- `30-scenarios/EVALUATION_METRICS.md` — outcome, multi-agent and reliability metrics.

## Codex operating model
- `40-codex/OPERATING_MODEL.md` — high-autonomy full implementation rules.
- `40-codex/CONTEXT_LOADING.md` — how to avoid context bloat.
- `40-codex/GOAL_MODE.md` — Goal mode workflow and completion discipline.
- `40-codex/PROGRESS_AND_BLOCKERS.md` — progress and blocker reporting.
- `40-codex/LEARNABILITY_REQUIREMENTS.md` — docs/code structure required so the owner can reverse-study the finished project.

## Roadmap and delivery
- `50-roadmap/ROADMAP.md`
- `50-roadmap/MILESTONES.md`
- `50-roadmap/RELEASE_CRITERIA.md`
- `50-roadmap/VERIFICATION_AUDIT.md` — direct local evidence for each `CODEX_GOAL.md` verification item and the hosted-CI boundary.

## GitHub
- `60-github/GITHUB_WORKFLOW.md`
- `60-github/REPOSITORY_SETUP.md`
- `60-github/RELEASE_WORKFLOW.md`

## Reverse learning / interview preparation
Codex maintains these as implementation advances:
- `90-learning/PROJECT_WALKTHROUGH.md`
- `90-learning/INTERVIEW_NOTEBOOK.md`
- `90-learning/TRACE_WALKTHROUGH.md`

## Planning
- `.agent/PLANS.md` defines ExecPlans.
- `.agent/exec-plans/active/` contains current plans.
- `.agent/exec-plans/completed/` contains finished plans.
