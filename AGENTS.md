# AGENTS.md

## 1. Purpose and scope

These instructions are **repository-specific** to `reliable-agent-lab`.

Do not copy them into a global Codex instruction file such as `~/.codex/AGENTS.md`.

This repository is both:

1. an engineering project for building a production-oriented tool-using agent; and
2. a learning project for the human maintainer.

Optimize for correct engineering **and** human understanding.

## 2. Project mission

The project demonstrates:

- LangGraph stateful orchestration;
- structured Tool Calling;
- MCP Client / Server integration;
- FastAPI-based agent services;
- asynchronous tool execution;
- structured input and output;
- retry, replan, and verification;
- checkpoint, interrupt, and resume;
- human-in-the-loop approval;
- permission-aware and idempotent side effects;
- tracing and observability;
- Python agent services integrating with a Java/Spring Boot backend.

The first scenario is microservice incident diagnosis and recovery. The repository is **not primarily an SRE product**; the incident environment exists to exercise agent engineering.

## 3. Core stack

Primary stack:

- Python 3.12
- LangGraph
- Pydantic
- FastAPI
- asyncio
- MCP Python SDK v2
- Java 21
- Spring Boot
- MySQL
- Redis
- Docker / Docker Compose
- Prometheus
- OpenTelemetry
- Jaeger

Do not introduce another agent framework without explicit human approval.

Examples that require approval:

- CrewAI
- AutoGen
- PydanticAI
- OpenAI Agents SDK
- Semantic Kernel

LangGraph is the primary orchestration framework. MCP is the primary protocol boundary between the agent runtime and external tools.

## 4. Explicit non-goals for V1

Do not expand V1 with:

- RAG;
- long-term memory;
- multi-agent orchestration;
- fine-tuning or RLHF;
- Kubernetes;
- local LLM hosting;
- complex frontend frameworks.

Avoid scope expansion unless it directly supports an accepted Issue.

## 5. Architecture boundaries

### agent/

Owns:

- AgentState;
- LangGraph topology;
- nodes and routing;
- domain schemas;
- retry and risk policies;
- agent-level orchestration.

It should depend on tool contracts, not concrete Spring Boot, Prometheus, or database implementation details.

### api/

Owns:

- FastAPI routes;
- incident API;
- approval API;
- SSE event streaming;
- request validation;
- API-level error mapping.

Do not place reasoning logic in API routes.

### mcp-servers/

Owns external tool integration.

Initial capability groups:

- observability;
- database;
- operations.

Read-only and mutating tools must remain clearly distinguishable.

### demo-service/

Owns the small Java/Spring Boot test environment.

Do not turn it into a full e-commerce system. Its purpose is to provide realistic backend behavior, MySQL/Redis integration, observability, and deterministic fault injection.

### scenarios/

Each scenario must define:

- fault;
- expected symptoms;
- expected evidence;
- ground-truth root cause;
- expected remediation;
- verification criteria.

Prefer deterministic scenarios.

## 6. Learning and teaching protocol

For architecture-critical agent concepts, default to **Teaching Mode**.

The goal is:

```text
understand -> human design -> implementation -> review
```

not:

```text
prompt -> generated code -> done
```

### Teaching Mode applies to

- AgentState design;
- LangGraph node and edge design;
- conditional routing;
- Tool Calling architecture;
- MCP client/server boundaries;
- structured output;
- asyncio concurrency;
- checkpoint and resume;
- interrupt and human-in-the-loop;
- retry vs replan;
- tool permissions;
- idempotency;
- verification strategy;
- observability architecture.

### Teaching Mode sequence

Before implementing a core concept:

1. Explain the engineering problem in plain language.
2. Explain the underlying concept before framework syntax.
3. Give a small example only if useful.
4. Ask the human to make the key design decision or write the core part.
5. Review the human attempt before rewriting it.
6. Explain trade-offs and failure cases.
7. Help finish production code only after the concept is understood.

If the human explicitly requests `implementation mode`, a complete implementation may be provided after a concise explanation.

### Progressive hints

When the human is stuck, escalate help gradually:

1. concept hint;
2. design hint;
3. interface or pseudocode skeleton;
4. partial implementation;
5. full implementation.

Do not jump to level 5 for architecture-critical work unless explicitly requested.

### Review before rewrite

When the human provides code or a design, first review:

- what is correct;
- what may fail;
- what can be simplified;
- what trade-offs exist;
- what should change and why.

Preserve good parts of the human design.

### Interview-oriented checks

After important features, briefly test understanding with questions such as:

- Why is this field in AgentState?
- Why is verification a separate node?
- Why does a timeout retry while verification failure replans?
- Why does this tool require approval?
- Why is MCP useful here instead of a direct Python import?
- What happens if the process crashes while waiting for approval?

Do not quiz the human on trivial boilerplate.

## 7. Human-owned decisions

Codex may teach, propose, and review, but must not silently replace these decisions:

- project scope;
- primary agent framework;
- AgentState conceptual design;
- graph node boundaries;
- MCP server boundaries;
- tool contracts;
- tool risk model;
- retry vs replan semantics;
- approval policy;
- idempotency strategy;
- verification strategy;
- scenario ground truth;
- public API compatibility;
- Git branch and release strategy.

## 8. Work Codex may implement aggressively

Codex may directly implement low-learning-value work after interfaces are clear:

- DTOs and data mapping;
- CRUD boilerplate;
- repository layers;
- Dockerfiles;
- Docker Compose updates;
- CI workflows;
- test fixtures and mock data;
- repetitive MCP tool implementations;
- documentation consistency updates;
- refactoring after architecture is agreed.

## 9. Agent design rules

### Explicit state

Keep important execution information in structured state. Store raw information rather than prompt-formatted text when possible.

### Small node responsibility

Prefer focused nodes such as:

- collect;
- diagnose;
- plan;
- risk_check;
- approve;
- execute;
- verify.

Avoid giant nodes that mix unrelated phases.

### Structured output

Critical model decisions must use typed schemas where possible, including Diagnosis, RemediationPlan, Action, and VerificationResult.

### Side effects

Read-only tools may usually execute automatically.

Mutating tools require explicit risk classification. High-risk operations require human approval.

Never add an unrestricted shell execution tool. Never allow arbitrary SQL mutation generated directly by the LLM.

### Retry vs replan

Retry transient failures such as timeouts or temporary tool unavailability.

Replan semantic failures such as an ineffective remediation or failed verification.

Permanent errors should fail explicitly.

### Verification

A successful tool response does not prove task success. After remediation, independently verify system state.

### Idempotency

Mutating actions must be safe against duplicate execution. Use action IDs or idempotency keys where appropriate.

## 10. Coding and test rules

### Python

Use Python 3.12, type hints, Pydantic models, and async APIs for IO-bound work.

Expected checks:

```bash
ruff check .
ruff format --check .
pytest
mypy .
```

Do not use bare `except:`. Do not silently swallow exceptions. External calls require explicit timeout behavior.

### Java

Use Java 21, Spring Boot, Maven, and constructor injection.

Expected test command:

```bash
mvn test
```

Do not place business logic in Controllers.

### Tests

Behavioral changes require tests. Use unit, integration, or scenario tests at the appropriate level.

Do not weaken tests just to make a broken implementation pass.

## 11. Git workflow

Detailed GitHub policy lives in `CONTRIBUTING.md`.

Core rules:

- never develop directly on `main`;
- never push directly to `main`;
- non-trivial work starts from an Issue;
- use a scoped feature/fix/docs/test branch;
- use Conventional Commits;
- all non-trivial changes enter `main` through a Pull Request;
- default merge strategy is Squash and Merge;
- never force-push or rewrite `main` history.

Codex must not push, open/merge PRs, tag releases, modify branch protection, change repository visibility, or change secrets unless explicitly requested.

## 12. Codex task workflow

For substantial tasks:

1. Read this file, the Issue/task, relevant docs, and nearby code.
2. Inspect `git status` and current branch before editing.
3. If on `main`, do not make implementation changes until a feature branch is used.
4. State a concise implementation plan.
5. Use Teaching Mode when the task touches human-owned agent concepts.
6. Implement the smallest change satisfying acceptance criteria.
7. Run focused tests, then affected project checks.
8. Inspect `git diff` and `git status`.
9. Report what changed, tests run, limitations, and the recommended next step.

Never claim a test passed unless it actually ran successfully.

## 13. Documentation

Architecture changes update `docs/ARCHITECTURE.md`.

Agent flow changes update `docs/AGENT_DESIGN.md`.

MCP boundary changes update `docs/MCP_DESIGN.md`.

Reliability policy changes update `docs/RELIABILITY.md`.

Learning outcomes may be recorded under `docs/learning/`.

README must describe behavior that actually exists. Do not mark roadmap items complete before implementation and testing.

## 14. Definition of done

A task is complete only when:

- acceptance criteria are satisfied;
- architecture rules are respected;
- new behavior has tests;
- relevant tests and checks pass;
- docs are current;
- no secrets or debug artifacts are present;
- the diff contains only task-related changes;
- remaining limitations are documented.

Prefer explicit, testable, inspectable behavior over clever abstractions or framework magic.
