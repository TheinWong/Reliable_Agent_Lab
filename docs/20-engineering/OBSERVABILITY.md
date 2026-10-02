# Observability

## Objective
A reviewer should be able to inspect one incident and understand:
- which agent delegated to which specialist;
- which tools were called;
- latency and failures;
- approval pause/resume;
- action execution;
- verification and final status.

## Tracing
Instrument at least:
- incident/API request;
- workflow run;
- supervisor decisions;
- specialist runs;
- model calls where supported;
- MCP tool calls;
- operations;
- verification.

Use correlation attributes such as:
- incident_id;
- run_id/thread_id;
- agent_role;
- tool_name;
- scenario_id;
- action_id;
- retry/replan count.

## Metrics
Useful metrics may include:
- incident duration;
- agent/model/tool latency;
- tool errors/timeouts;
- number of specialist delegations;
- number of replans;
- scenario resolution rate;
- token usage when available.

## Logs
Use structured logs with correlation ids. Avoid logging secrets or full unbounded model/tool payloads.

## Demo artifact
The final README/docs should include at least one trace screenshot or exported trace walkthrough if feasible.
