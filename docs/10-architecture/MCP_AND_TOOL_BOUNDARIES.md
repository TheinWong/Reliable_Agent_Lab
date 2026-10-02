# MCP and Tool Boundaries

MCP separates the LangGraph orchestrator from external capabilities. The four groups below run as separate Streamable HTTP MCP servers inside Compose; none is published to the host. Investigation specialists each receive one read-only client. Only the approval-gated execution node receives the Operations client; the Verifier receives a separate read-only recovery client.

| Group | Tool | Input | Typed result | Access |
| --- | --- | --- | --- | --- |
| Metrics | `query_service_metrics` | `service="order-service"` | bounded `MetricsSnapshot` from Java | Metrics specialist, read-only |
| Metrics | `probe_cache_recovery` | `service="order-service"` | fault state and two fresh order-read sources | Verifier, read-only application GETs |
| Metrics | `probe_mysql_recovery` | `service="order-service"` | MySQL fault state and two fresh order-read sources | Verifier, read-only application GETs |
| Metrics | `probe_inventory_recovery` / `probe_payment_recovery` | `service="order-service"` | downstream fault state and fresh checkout-preview result | Verifier, read-only application GETs |
| Logs | `query_recent_logs` | `service="order-service"` | at most 100 structured events in `LogsSnapshot` | Logs specialist, read-only |
| Traces | `query_service_traces` | `service="order-service"` | bounded recent order-read/checkout-preview `TraceSnapshot`, including real inventory/payment spans; empty and unavailable differ | Trace specialist, read-only |
| Operations | `reset_redis_fault` | UUID `action_id`, `scope="local-demo"` | `ResetFaultResult` with `duplicate` marker | approval-gated execution node only |
| Operations | `reset_mysql_fault` | UUID `action_id`, `scope="local-demo"` | controlled read-fault reset and `duplicate` marker | approval-gated execution node only |
| Operations | `reset_inventory_latency` / `reset_payment_5xx` | UUID `action_id`, `scope="local-demo"` | named downstream reset and `duplicate` marker | approval-gated execution node only |

The operations server is disabled unless `RAL_DEMO_OPERATIONS_ENABLED=true`. Its action/dependency ledger prevents duplicate execution within one server process. The API persists approvals and a PostgreSQL action execution record keyed by deterministic action ID; a completed record lets graph replay skip a second MCP operation. If a crash occurs after the external call but before that record is completed, the same-ID retry is safe for these specific controlled resets because the Java endpoints are idempotent. This does not prove general exactly-once side effects. The S1–S4 scripts' direct fault injection/cleanup is a test fixture, not an agent capability. No unrestricted shell, arbitrary SQL/URL, or Docker control is exposed.

## Contracts and failures

Inputs and outputs are Pydantic-validated. Each server's tools have SDK read-only/idempotency annotations; each call has a client timeout, and Java reads have a downstream HTTP timeout. Clients distinguish validation, timeout, dependency, policy, and operation failures via `ToolErrorCode`. Empty logs are a valid typed result, not a transport failure. The S1 operation retries once only for timeout/dependency failures with the same action ID; other operation errors fail explicitly. Investigation failures never become empty evidence.

`make mcp-smoke` checks all four real transports and duplicate-safe Redis reset. Contract tests exercise all four reset tools, SDK client/server calls, tool lists/annotations, payloads, invalid service/scope, disabled operations, timeout classification, empty logs, and fresh recovery probing. S1–S4 exercise investigation, reset, and verification through MCP in the running graph.

## Remaining boundaries

The Trace tool queries only Jaeger's recent order-read and checkout-preview traces, caps results and response bytes, and never fabricates spans. The operation client forwards a validated W3C `traceparent` through its typed MCP argument to Java's reset endpoint, so the Java DELETE span joins the resumed Agent trace. Investigation agents cannot obtain the Operations client through their injected interfaces. The current policy always requires approval before S1–S4 mutations; the loopback-only demo API has no production authentication. S2 is a controlled application read fault, not a physical MySQL outage. General exactly-once action semantics for non-idempotent external systems, replan, and richer retry policy remain open.
