# Agent Design

## Goal

Make the agent execution graph explicit, inspectable, testable, and explainable.

## Baseline graph

```text
START
  |
  v
collect
  |
  v
diagnose
  |
  v
plan
  |
  v
risk_check
  |
  +-------------------+
  |                   |
  v                   v
execute             approve
  |                   |
  +---------+---------+
            |
            v
          verify
         /      \
        v        v
      END      replan
                |
                +----> plan or diagnose, depending on evidence
```

The exact replan destination is a human-owned design decision and should be justified by failure semantics.

## Candidate state model

The human maintainer should design the final fields. A candidate conceptual decomposition is:

- immutable incident input;
- collected evidence;
- diagnosis;
- remediation plan;
- proposed actions;
- approval status;
- action execution results;
- verification result;
- retry/replan counters;
- execution metadata.

Do not treat this list as a final schema without discussion.

## Node responsibilities

### collect

Gather independent evidence such as:

- service health;
- logs;
- metrics;
- dependency status.

Prefer concurrent IO when calls are independent.

### diagnose

Produce a typed diagnosis containing at least:

- probable root cause;
- supporting evidence references;
- affected component;
- confidence or uncertainty information.

### plan

Produce a bounded remediation plan with typed actions.

### risk_check

Classify proposed actions by policy. It should not delegate the entire safety decision to free-form LLM output.

### approve

Pause the graph for required human approval and resume deterministically.

### execute

Execute only allowed, typed, bounded actions.

### verify

Re-query the environment after remediation. Never equate `tool returned success` with `incident resolved`.

## Structured outputs

Critical decisions should use Pydantic-backed structured outputs rather than free-form parsing.

Initial models may include:

- Incident
- Evidence
- Diagnosis
- RemediationPlan
- Action
- ActionResult
- VerificationResult

## Prompt policy

Prompts should remain focused on reasoning tasks. Deterministic policies such as approval requirements, maximum retries, and allow-lists belong in code/configuration rather than hidden prompt instructions.

## Failure semantics

Distinguish:

- transient tool failure -> retry;
- semantic remediation failure -> replan;
- permanent invalid request -> fail;
- high-risk action -> pause for approval.

This distinction is a core learning objective.
