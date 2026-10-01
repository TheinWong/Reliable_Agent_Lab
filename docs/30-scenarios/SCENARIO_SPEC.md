# Scenario Specification

Scenarios are deterministic test fixtures and product demos.

Each scenario must define:
- `id`
- `title`
- `description`
- services involved
- preconditions
- fault injection action
- observable symptoms
- expected evidence by source (metrics/logs/traces/health)
- ground-truth root cause
- expected/allowed remediation actions
- forbidden actions if relevant
- verification criteria
- reset/cleanup action
- expected risk/approval behavior

## Properties
- injection and reset should be repeatable;
- scenarios must not depend on uncontrolled internet services;
- ground truth must be machine-readable enough for regression evaluation;
- every mutating action must only affect the local demo environment.
