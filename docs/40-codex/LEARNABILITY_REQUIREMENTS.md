# Learnability Requirements

The human owner intends to learn the project after Codex completes substantial implementation. Therefore the repository must be easy to reverse-study.

## Required learning artifacts
Maintain:
- `docs/90-learning/PROJECT_WALKTHROUGH.md`
- `docs/90-learning/TRACE_WALKTHROUGH.md`
- `docs/90-learning/INTERVIEW_NOTEBOOK.md`

## Code properties
- clear domain names;
- no unexplained framework magic around core flow;
- explicit graph and state definitions;
- tool contracts close to implementations;
- comments/docs for reliability decisions;
- representative integration tests that can be followed as executable examples.

## PROJECT_WALKTHROUGH must eventually explain
1. repository map;
2. how an incident enters the system;
3. how supervisor delegates;
4. how specialist results rejoin;
5. how diagnosis/remediation works;
6. how approval pauses and resumes;
7. how MCP calls map to demo services;
8. how verification works;
9. how persistence/idempotency works;
10. how to reproduce one scenario locally.

## INTERVIEW_NOTEBOOK
Do not merely generate trivia. Record project-specific questions such as:
- why multi-agent instead of one agent with all tools;
- state/handoff design;
- Send/subgraph/async choices;
- conflicting specialist evidence;
- MCP vs direct Python calls;
- retry vs replan;
- HITL persistence;
- verifier independence;
- token/latency trade-offs;
- failure modes and limitations.
Leave room for the owner to write their own answers later.
