---
name: pipeline-orchestration
description: Use when coordinating multiple specialist agents through an ordered SDLC pipeline with gates and retries.
---

# Pipeline Orchestration

## Contract between stages

Every stage consumes named input artifacts and produces named output artifacts. A stage
is only runnable when all of its declared inputs exist in the run state. Treat a missing
input as a bug in the pipeline, not as something to improvise around.

## Control flow

- **Advance** when the stage succeeds and produced all of its declared outputs.
- **Retry** when testing fails: hand the failure report back to the coding stage and
  re-run testing. Bound the number of retries so a broken change cannot loop forever.
- **Block** when a gate returns `pending`: stop the run and surface what is being waited on.
- **Stop** when a stage fails in a way retries cannot fix, or when a gate rejects.

## Auditability

Append one event per stage attempt: stage, agent, status, produced artifacts, timestamp.
The event log is the deliverable that lets a human reconstruct what the agents did.
