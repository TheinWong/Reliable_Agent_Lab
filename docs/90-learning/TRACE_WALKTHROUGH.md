# Trace Walkthrough

ExecPlan 0005 added real OTLP spans; 0006 extends the same checks to S2–S4. Run any `make scenario SCENARIO=...` from README with Compose running. Each prints Jaeger IDs for the investigation and resumed execution traces; S3/S4 also print the faulted downstream HTTP trace ID. Open `http://127.0.0.1:16686` and search `agent-api`, or query Jaeger's `/api/v3/traces/{traceId}`. Jaeger stores this demo data in memory, so IDs do not survive a Jaeger restart.

## Representative scenario
Scenario ID: `s1-redis-unavailable`
Fault: controlled Redis access failure inside order-service
Expected root cause: Redis cache dependency unavailable while MySQL remains authoritative
Expected remediation: reset the controlled fault, then prove cache repopulation and a subsequent hit

## Observed span shape
The S1 scenario on 2026-10-01 verified two traces for one `incident_id`/`run_id` because it restarts `agent-api` during the approval pause:

```text
incident.run
  agent.supervisor.delegate
  agent.metrics / agent.logs / agent.trace (parallel branches)
    tool.query_service_metrics / tool.query_recent_logs / tool.query_service_traces
  agent.supervisor.fuse
  agent.remediation -> policy.risk -> approval.gate (interrupt)

incident.resume (new process and trace, same incident_id/run_id)
  approval.gate -> operation.execute
    tool.reset_redis_fault
      order-service: DELETE /internal/faults/redis-unavailable
  agent.verifier -> tool.probe_cache_recovery
```

`scripts/verify_traces.py` queries Jaeger's v3 API after each scenario and asserts actual spans, parent/child links, the shared run ID, and the named Java DELETE span's `parentSpanId` equal to the Python reset-tool span ID. S2–S4 substitute their named reset/probe in the resumed branch. For S3/S4, `scripts/verify_downstream_trace.py` first proves a post-injection inventory-service span lasting >=500 ms or payment-service span returning HTTP 5xx within the same order checkout-preview trace. The Java order-read path also emits `GET /api/orders/{id}` and cache/database spans. Trace MCP queries recent order-read and checkout-preview traces through the v3 API. It returns `available=true` with an empty list when the query succeeds but finds nothing, and `available=false` when Jaeger is unreachable or its response is invalid. SSE events remain a separate audit view, not tracing evidence.

## Key attributes
Python spans include bounded `ral.incident_id`, `ral.run_id`, `ral.agent_role`, `ral.tool_name`, and `ral.action_id` where relevant. The operation client forwards the current W3C `traceparent` as a validated MCP argument; Operations MCP sends it on the narrow Java reset request. Java's OpenTelemetry agent continues that trace. The approval pause itself is a checkpoint boundary, not one continuous trace across process restart.

## What the trace proves and does not prove
The runtime trace proves S1 delegation, concurrent branch spans, MCP tool calls, a restarted approval/resume segment, and one cross-service reset span. It does not prove that every Metrics/Logs/Trace read is one continuous distributed trace, production-grade authentication, persistent trace storage, or a successful semantic replan.
