# Configuration and Secrets

## Principles
- Commit `.env.example`, never `.env`.
- Use environment variables for model/API credentials.
- Give demo databases local-only non-sensitive defaults when practical.
- Keep remote model provider configuration replaceable.
- Do not log credentials.

## Current v0.1 configuration
`.env.example` contains only loopback Compose host ports. Compose supplies local demo database credentials and internal MCP/telemetry URLs; they are not production secrets. The deterministic Agent graph requires no model key. Do not mistake the example file for a live-model configuration.

## Future/opt-in configuration groups
- model provider/model name/base URL/key;
- agent time/step limits;
- MCP server endpoints/transports;
- PostgreSQL state database;
- MySQL/Redis demo dependencies;
- telemetry collector/Jaeger/Prometheus endpoints;
- live-eval enablement.

## Missing credentials
Core deterministic tests do not require live LLM credentials. A live-model adapter/test command is not implemented in v0.1; it must be explicitly designed, credential-gated, and documented before use. Do not claim that the current scenarios evaluate model quality.
