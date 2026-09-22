# MCP Design

## Why MCP is used

MCP is used to decouple the agent runtime from concrete external integrations.

The important design goal is not "use MCP because it is popular". The goal is that agent reasoning code depends on stable tool contracts while the implementation behind those contracts can change.

Example:

```text
LangGraph -> query_logs contract -> MCP server -> local files now / Loki later
```

The agent graph should not need to change when the logs backend changes.

## SDK baseline

Use the current stable MCP Python SDK v2 line.

The first implementation should use the official SDK and one well-understood transport. Add other transports only when there is a concrete need.

## Initial server boundaries

### observability

Read-only tools such as:

- query_service_health
- query_logs
- query_metrics
- get_dependency_status

### operations

Mutating tools such as:

- recover_redis
- reset_fault
- restart_demo_service

### database

Optional later server for narrowly scoped read-only inspection.

Do not expose arbitrary SQL mutation.

## Tool contract rules

Each tool should define:

- typed input schema;
- typed output schema;
- timeout behavior;
- error representation;
- read-only vs mutating classification;
- idempotency behavior if mutating;
- target allow-list.

## Error model

Do not return ambiguous strings like `failed` when structured error details are available.

Useful categories include:

- timeout;
- unavailable;
- invalid_argument;
- not_found;
- permission_denied;
- conflict;
- internal_error.

Map protocol/library errors into stable project-level tool errors before the graph reasons about them.

## Security boundary

MCP does not make a tool safe by itself.

Safety still requires:

- bounded tool implementation;
- allow-listed targets;
- typed arguments;
- risk classification;
- approval policy;
- idempotency;
- audit/tracing.

Never add an unrestricted shell tool for convenience.
