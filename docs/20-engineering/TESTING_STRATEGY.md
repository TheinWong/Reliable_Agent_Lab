# Testing Strategy

## Testing pyramid

### Unit tests
Cover:
- state/model validation;
- routing decisions;
- risk policy;
- retry classification;
- idempotency helpers;
- specialist report normalization;
- scenario parsing.

### Contract tests
For each MCP tool:
- valid request/result;
- validation failure;
- empty result where applicable;
- timeout/transient failure;
- dependency failure;
- policy rejection for operations.

### Integration tests
Cover:
- Agent API -> graph runtime;
- supervisor -> specialists;
- graph -> MCP server;
- HITL pause/resume;
- checkpoint restart/resume;
- operations idempotency.

### Scenario tests
Run deterministic end-to-end faults with ground truth. Scenario tests are the primary evidence that the agent system works beyond mocks.

## LLM nondeterminism
Where possible separate deterministic control-plane tests from model-quality tests.
Use recorded/fake model outputs for graph mechanics and real-model scenario runs for end-to-end validation.
Avoid CI that is flaky or requires paid credentials for every pull request. Provide an opt-in live suite.

## Minimum CI gates
- Python lint/format/type/unit tests;
- Java build/tests;
- configuration validation;
- Docker Compose config/build smoke where feasible;
- no committed secret scan if a lightweight tool is adopted.
