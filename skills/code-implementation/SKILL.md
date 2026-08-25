---
name: code-implementation
description: Use when writing or changing code so the diff stays minimal, conventional and reviewable.
---

# Code Implementation

## Rules

- Implement one planned task at a time and keep the change surgical: no unrelated
  refactors, no speculative abstractions, no dead scaffolding.
- Match the surrounding code — naming, error handling, logging and comment style.
- Reuse what the repository already depends on; adding a dependency needs a reason in
  the plan.
- Never commit secrets, tokens or credentials, and validate untrusted input at the
  boundary where it enters the system.
- Run the fastest relevant check (unit test, type check, linter) before moving to the
  next task, so failures point at one change.

## Output

A changeset: files touched, one-line rationale per task, and any follow-up left behind.
