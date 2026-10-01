# State and Handoffs

## Principle
Shared workflow state should be structured and minimal. Preserve raw facts separately from model conclusions.

## Suggested domain models
The exact implementation may evolve, but should preserve these concepts:

### Incident
- id
- service(s)
- symptom/alert
- severity
- created_at
- scenario_id when applicable

### Evidence
- source type
- source/tool
- timestamp/time range
- structured payload or bounded excerpt
- provenance/reference

### SpecialistReport
- agent role
- findings
- evidence references
- hypotheses
- confidence
- missing_information

### Diagnosis
- suspected root cause
- affected component(s)
- evidence references
- confidence
- alternatives

### RemediationPlan
- action type
- target
- typed parameters
- risk classification input
- expected effect
- rollback description

### ActionExecution
- action id / idempotency key
- status
- attempts
- tool result
- timestamps

### VerificationResult
- status: resolved / partially_resolved / unresolved
- fresh evidence
- criteria results
- explanation

## Handoff rules
- Agents hand off typed reports, not unrestricted hidden reasoning.
- Handoff payloads should be size-bounded.
- Evidence provenance must survive handoffs.
- Do not duplicate large log/trace bodies in every state field.
- Use references/summaries where practical.
- Persist enough state to resume after an approval interruption.

## Checkpoint concerns
At minimum persist the incident identity, current graph position, accumulated reports, proposed plan, approval status and action execution/idempotency records needed for safe resume.
