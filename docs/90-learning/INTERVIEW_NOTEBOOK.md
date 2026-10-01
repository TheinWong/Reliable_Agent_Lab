# Interview Notebook

> Codex: keep questions aligned to actual implementation. Do not fabricate capabilities. Leave concise code/doc references; the human owner can later write personal answers.

## Multi-agent architecture
- Why does this project use multiple agents instead of one agent with every tool?
- Which agent boundaries are justified by context, tool or permission isolation?
- How does Supervisor decide which specialists to invoke?
- Are specialist agents actually concurrent? Where is this implemented?
- What happens when specialist evidence conflicts?
- What is passed between agents: raw text, messages, or typed state?
- Why are Remediation and Verification separate?

## LangGraph/runtime
- Why LangGraph rather than CrewAI/AutoGen or a handwritten loop?
- Which graph primitives are used and why?
- What state is checkpointed?
- How does execution resume after approval/process restart?
- Where are loop limits enforced?

## MCP/tools
- Why MCP instead of direct Python functions?
- How are tool schemas typed and validated?
- How do timeout/transient/permanent failures differ?
- How are read-only and mutating tools isolated?

## Backend
- Why FastAPI and asyncio?
- How does SSE behave if a client disconnects?
- Does the incident continue without an SSE client?
- How do Python agents interact with Java services?

## Reliability/security
- Retry vs replan?
- How is idempotency implemented?
- What actions require approval and why?
- How do you prevent arbitrary shell/SQL execution?
- What happens if an MCP server is unavailable?

## Observability/evaluation
- How do you trace an incident across agents/tools/services?
- How do you test graph mechanics without paid model calls?
- What metrics show multi-agent benefit/cost?
- When could multi-agent be slower or worse than single-agent?

## Limitations
- What does the project not prove about real production SRE?
- What would need to change for Kubernetes/large-scale production use?

## First vertical slice: evidence-backed notes
- Why is MySQL authoritative? Redis is an optimization; S1 must preserve reads while surfacing a dependency failure. See ADR-005 and `OrderQueryService`.
- Why not `@Cacheable`? The explicit path preserves hit, miss, read error, skipped write, and write error for tests and telemetry.
- What does the graph prove now? Supervisor fan-out to three role-specific specialist nodes, typed reports, parallel execution, and evidence fusion. The Trace specialist reads bounded Jaeger evidence and reports empty/unavailable separately; S1 queries real Jaeger spans rather than inferring trace success from SSE.
- How is a trace continued across approval restart? It is not one continuous process span: the investigation and resumed execution are two traces linked by `ral.incident_id` and `ral.run_id`. The approved reset forwards validated W3C `traceparent` through Operations MCP so the Java DELETE span is a child of the Python reset-tool span in the resumed trace. See `scripts/verify_traces.py`.
- Why does the Supervisor require Metrics and Logs agreement for S1? Current fault state alone could be active without a failed order read; a stale log from before reset could mislead diagnosis. `LogsAgent` scopes failures after the latest active injection, while `supervisor_fuse` requires both sources.
- How is recovery proved? The independent Verifier uses the read-only MCP recovery probe to check fault reset, a fresh database read, and a subsequent `CACHE` hit. The S1 script then performs its own read pair; container health or operation success alone is insufficient.
- What is now durable? LangGraph checkpoints and API incident/event resources live in PostgreSQL. The S1 script pauses, restarts agent-api, reads the same incident/events, and resumes through the approval endpoint. The background task registry and MCP operations duplicate ledger remain process-local.
- Why force approval for a local reset? The server-side v0.1 policy conservatively gates every mutation, making the permission boundary observable; this is not a production authorization system.
- What prevents duplicate mutation? The approval endpoint returns existing state for an identical repeated decision; the action ID is stable, PostgreSQL stores the S1 action outcome and skips an already-completed call on graph replay, the Operations server suppresses same-process duplicates, and Java reset is idempotent. A crash between external execution and ledger completion can still replay that idempotent reset; this is narrower than a general exactly-once guarantee.
- What does S2 actually prove? It injects a controlled application-boundary MySQL read failure for an uncached order, sees an explicit 503/metric/log, diagnoses only when current Metrics and Logs agree, then independently verifies a fresh database read and cache hit after an approved reset. It does not prove recovery from a real MySQL network outage or exhausted pool.
- Why do S3/S4 require three evidence sources? Current fault state identifies the active injection, but a stale log or span alone can mislead. Supervisor requires the matching order event and real downstream Jaeger span to start after the fault activation timestamp. The trace proves the inventory/payment call is in an order checkout-preview trace.
- What is the S4 payment boundary? The service exposes only a stateless authorization preview. The controlled 503 produces an upstream 502; no real charge or external payment system is involved.
- How is downstream recovery checked? The approved named reset is not proof. A separate read-only verifier checks the downstream fault state and a fresh checkout preview; S3 additionally requires inventory latency below 500 ms, while S4 requires authorized payment preview. Both scenario scripts verify the Java DELETE span is parented to the Python operation-tool span.
