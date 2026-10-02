# Project Brief

## Audience
The project is designed to be credible evidence for roles such as:
- Agent Engineer / Agent Application Engineer;
- Agent Backend Engineer;
- Agent Platform / Harness Engineer;
- AI Application Backend Engineer.

## Capability gaps this project should demonstrate
Existing experience may already prove Memory, Context Engineering, RAG and Eval. This project deliberately emphasizes different evidence:
- multi-agent coordination;
- LangGraph stateful orchestration;
- Tool Calling and MCP;
- Python FastAPI backend engineering;
- asynchronous execution;
- state persistence and resumption;
- human approval and permission boundaries;
- reliable tool execution;
- observability;
- integration with a Java/Spring Boot backend.

## Product story
A small e-commerce-like microservice environment intentionally produces faults. A supervisor coordinates specialized read-only investigation agents, delegates a proposed recovery to a remediation planner, routes risky actions through approval, executes through constrained operations tools, and uses an independent verifier to decide whether the system actually recovered.

## Engineering story
The project should be understandable as software, not merely as prompts:
- typed data contracts;
- visible graph topology;
- explicit state;
- bounded side effects;
- tests;
- telemetry;
- scenario ground truth;
- reproducible local deployment.
