# Prompt and Model Policy

The following is the policy for a future optional model adapter. The v0.1 incident workflow is deterministic and has no live model calls or prompt evaluation; its multi-agent boundaries are graph roles, separate contexts, typed reports, and scoped MCP capabilities.

## Model role
LLMs perform interpretation, evidence synthesis, planning and typed decisions where deterministic code is insufficient.
Deterministic validation, permission rules, idempotency and hard safety boundaries remain in code.

## Provider abstraction
Do not hard-wire the domain logic to one model provider. Keep provider/model configuration external and centralize adapter choices.

## Structured outputs
Critical outputs such as SpecialistReport, Diagnosis, RemediationPlan and VerificationResult must be schema-validated.
Do not parse safety-critical decisions from arbitrary prose if a typed contract is available.

## Prompt versioning
Keep non-trivial prompts in identifiable modules/files so changes can be reviewed/tested.
Prompt changes that affect behavior require scenario/live-eval evidence where practical.

## Reasoning privacy
Do not depend on exposing private chain-of-thought. Persist concise conclusions, evidence references and decision rationales suitable for logs/audits.

## Tests
CI graph/control-flow tests should work with deterministic fake model responses.
Live model scenario tests would be a separate opt-in suite when an adapter and credentials are available; no such suite is claimed for v0.1.
