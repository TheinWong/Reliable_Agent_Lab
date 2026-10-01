# Multi-Agent Design

## Why multi-agent here
The split must be justified by context/tool/permission boundaries and concurrency, not by role-play.

### Benefits expected
- smaller context per specialist;
- narrower tool sets;
- parallel independent investigation;
- read-only investigators separated from mutating operations;
- remediation separated from verification;
- inspectable handoffs and traces.

## Supervisor
The Supervisor should not become a god-agent with every low-level tool.
It owns:
- incident interpretation;
- delegation choice;
- evidence sufficiency;
- conflict resolution between specialist reports;
- root-cause hypothesis;
- workflow-level replan/termination.

It should receive structured specialist reports, not raw unlimited telemetry whenever avoidable.

## Specialist agents
### Metrics Agent
Inputs: incident scope, service names/time window.
Outputs: anomalies, evidence, hypotheses, confidence, missing evidence.
Tools: metrics and health only.

### Logs Agent
Outputs error patterns, representative evidence, suspected components, confidence.
Tools: log query/search only.

### Trace Agent
Outputs slow/error spans, service path, suspected bottleneck/failing dependency.
Tools: trace/topology only.

## Remediation Agent
Receives normalized incident + fused diagnosis + evidence summary.
Produces a typed RemediationPlan with action, target, parameters, risk hint, expected effect and rollback idea.
The policy layer, not the LLM alone, decides whether approval is mandatory.

## Verifier Agent
Runs after execution and should not simply accept the remediation agent's claim.
It may know the action taken but should make its resolution decision from fresh evidence and explicit criteria.

## Parallelism
Metrics/Logs/Trace are independent in normal investigations and should support fan-out/fan-in.
Use LangGraph graph primitives for orchestration. `asyncio` may be used inside a node/tool implementation for independent I/O; do not confuse node-level async with workflow delegation.

## Conflict handling
When specialist reports disagree:
1. preserve each report and evidence;
2. have Supervisor identify the conflict;
3. request targeted follow-up evidence if budget permits;
4. reduce confidence rather than invent consensus;
5. escalate/stop safely if a risky remediation is not defensible.

## Anti-patterns
- agents passing large raw chat histories to each other;
- every agent having all tools;
- specialists that only restate the same prompt;
- remediation and verification being the same self-confirming call;
- fixed sequential invocation when evidence collection is independent;
- adding more agents without a distinct responsibility or boundary.
