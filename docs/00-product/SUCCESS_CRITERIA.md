# Success Criteria

The project succeeds when a reviewer can clone the repository and find evidence that the system is both a real multi-agent application and a real backend-engineering project.

## Reviewer-visible evidence
A reviewer should be able to identify:
1. distinct agent roles with a reason for each split;
2. structured handoffs instead of free-form conversational chaining;
3. specialist tool isolation;
4. parallel evidence gathering;
5. a standard MCP tool boundary;
6. a FastAPI API and event stream;
7. explicit failure handling and persisted workflow state;
8. human approval for at least one mutating path;
9. a separate verifier;
10. end-to-end traces;
11. deterministic scenarios with ground truth;
12. Java/Spring Boot integration;
13. tests and CI;
14. documentation that explains design trade-offs.

## Anti-success
The project does not count as successful if it is only:
- a prompt calling several named agents sequentially;
- a collection of mocked tools with no real demo service;
- a single-agent ReAct loop relabeled as multi-agent;
- a README that claims capabilities not exercised by tests;
- a framework showcase with no explanation of boundaries or failure semantics.
