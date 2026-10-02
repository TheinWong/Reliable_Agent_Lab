# Changelog

## v0.1.0 — public MVP code (unreleased; no tag)

- LangGraph Supervisor with concurrent, role-scoped Metrics, Logs and Trace investigations; typed reports and deterministic evidence fusion.
- Four MCP servers separating read-only investigation/recovery probes from approval-gated named operations.
- FastAPI incident, durable SSE event, and approval APIs backed by PostgreSQL resources and LangGraph checkpoints.
- Java 21 order, inventory and payment-preview services with MySQL-authoritative Redis cache-aside behavior and four controlled fault scenarios.
- OpenTelemetry/Jaeger checks for Agent/tool spans, real downstream HTTP spans and Java reset parentage.
- S1–S4 scripts covering injection, ground-truth diagnosis, API restart/resume, permitted reset, independent recovery and duplicate-approval safety; a four-case evaluation command.
- Local clean-worktree and hosted GitHub Actions verification are recorded in [`docs/50-roadmap/VERIFICATION_AUDIT.md`](docs/50-roadmap/VERIFICATION_AUDIT.md).

Limitations: this is a local controlled demo without production authentication, actual payment charges, real MySQL network-outage simulation, semantic replan, a live-model adapter, or general exactly-once side-effect guarantees. Hosted CI has passed; a public tag and release have not been published.
