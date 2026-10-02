# API Conventions

## REST
Use resource-oriented endpoints and typed request/response models.
Return stable machine-readable error codes plus human-readable messages.
Do not expose raw stack traces to API clients.

## Incident lifecycle
The incident creation request should return an incident/run identifier quickly rather than blocking for the whole agent workflow.
Status reads and SSE events should reference the same correlation identity.

The implemented S1 statuses are `pending`, `running`, `awaiting_approval`, `completed`, and `failed`. `POST /api/incidents/{id}/approval` accepts the proposed `action_id` and an `approved` boolean. A mismatched, conflicting, or non-pending decision returns `APPROVAL_CONFLICT` (HTTP 409); an identical repeated decision returns the current resource without launching a second action.

## SSE
Events should be typed, for example:
- incident.created
- delegation.started / completed
- tool.started / completed / failed
- diagnosis.updated
- approval.required / decided
- remediation.started / completed
- verification.completed
- incident.resolved / failed

SSE client disconnect must not implicitly cancel the durable incident workflow unless explicitly designed/documented.
The current stream replays persisted events and closes at an active `approval.required` or terminal event. Reconnecting after approval replays the event history, including the decision and final verification.

## Idempotent API behavior
Mutating approval/action endpoints should reject duplicates or behave idempotently where retries are expected.

## Versioning
Avoid premature public API version proliferation. If a `/api/v1` prefix is chosen, use it consistently.
