# Dependency Policy

Before adding a dependency:
1. state the capability it provides;
2. check whether the standard library or an existing dependency is sufficient;
3. prefer maintained and well-documented packages;
4. pin/lock versions reproducibly;
5. avoid adding overlapping frameworks.

## Core expected dependencies
The implementation may choose exact packages/versions consistent with current compatibility, but the architectural set is expected to center on:
- LangGraph;
- FastAPI / ASGI stack;
- Pydantic;
- MCP Python SDK;
- OpenTelemetry libraries;
- database/checkpoint drivers;
- pytest / Ruff / type checker.

Avoid convenience packages that hide core project behavior unless they materially reduce risk or complexity.
