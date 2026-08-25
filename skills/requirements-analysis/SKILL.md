---
name: requirements-analysis
description: Use to turn a context pack into numbered, testable requirements with acceptance criteria and explicit non-goals.
---

# Requirements Analysis

## Rules

- One requirement per statement, numbered `R1`, `R2`, ... so later stages can reference them.
- Every requirement needs an acceptance criterion phrased as an observable outcome
  ("`orchestrator run` exits non-zero when the gate is pending"), not an implementation
  detail ("add an if statement").
- Separate **must** from **should**; a *should* never blocks the pipeline.
- List non-goals. Scope you write down is scope nobody has to argue about later.
- Record assumptions and open questions. An open question that blocks a *must*
  requirement stops the stage — ask the requester.

## Output

```
R1 (must) <requirement> — accept when <observable outcome>
R2 (should) ...
Non-goals: ...
Assumptions: ...
Open questions: ...
```
