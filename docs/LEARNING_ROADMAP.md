# Learning Roadmap

This roadmap is organized by project milestones. Do not try to master every framework before writing code.

## Stage 1 - Python agent backend fundamentals

Learn:

- Python typing;
- Pydantic;
- FastAPI basics;
- async/await;
- asyncio.gather;
- exception handling;
- REST API boundaries;
- SSE basics.

Human must understand:

- why async helps IO-bound work;
- event-loop intuition;
- API vs domain responsibility;
- structured validation.

Codex may help with:

- route boilerplate;
- test scaffolding;
- serialization;
- middleware after interfaces are understood.

## Stage 2 - Faultable Spring Boot service

Learn/review:

- Spring Boot layers;
- MySQL persistence;
- Redis caching;
- Actuator;
- Docker Compose networking;
- deterministic fault injection.

Human must design:

- service behavior;
- Redis role;
- fault symptoms;
- ground truth.

Codex may implement much of the CRUD and test boilerplate.

## Stage 3 - LangGraph core

Learn:

- state;
- node;
- edge;
- conditional routing;
- graph compilation/execution;
- structured output;
- checkpoint concepts.

Human must design:

- AgentState;
- node boundaries;
- routing conditions;
- verify/replan semantics.

Codex should use Teaching Mode.

## Stage 4 - MCP

Learn:

- client/server boundary;
- tool schema;
- transport choice;
- typed errors;
- timeout behavior;
- why MCP is preferable to direct imports for replaceable integrations.

Human should implement or closely pair on the first MCP server.

Codex may help migrate repetitive tools after the pattern is understood.

## Stage 5 - Reliability and human-in-the-loop

Learn:

- retry vs replan;
- bounded execution;
- checkpoint/resume;
- human approval;
- risk classification;
- idempotency;
- post-action verification.

These are core interview topics. Do not treat them as black boxes.

## Stage 6 - Observability and regression quality

Learn:

- structured logging;
- traces and spans;
- metrics;
- correlation IDs;
- scenario tests;
- basic agent evaluation.

Goal: explain not only what the agent did, but how to prove it behaved correctly.

## Suggested learning notes

Create notes under `docs/learning/` as concepts are completed:

```text
01-langgraph-state.md
02-agent-routing.md
03-mcp-basics.md
04-async-tool-calling.md
05-structured-output.md
06-human-in-the-loop.md
07-checkpoint-resume.md
08-retry-vs-replan.md
09-agent-observability.md
```

Each note should answer:

1. What problem does this solve?
2. How does it work?
3. How is it used here?
4. What alternatives exist?
5. What mistake or trade-off did I encounter?

Prefer that the human writes the first draft and Codex reviews it.
