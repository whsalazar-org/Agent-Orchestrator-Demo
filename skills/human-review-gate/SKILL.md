---
name: human-review-gate
description: Use before deployment to package a change for human review and to block the pipeline until a decision is recorded.
---

# Human Review Gate

## Review package

- **What changed** and **why**, in the reviewer's language.
- Requirement traceability: `R1 -> T1 -> files -> test`.
- Test evidence: which checks ran and their results.
- Risk, blast radius and rollback plan.
- The specific questions you want the reviewer to answer.

## Rules

- The gate is blocking. `pending` means the pipeline stops, not that it proceeds
  optimistically.
- Only a named human may set `approved` or `rejected`; an agent recording its own
  approval defeats the gate.
- Green CI is evidence, not approval.
- On rejection, carry the reviewer's comments back to the coding stage verbatim.

## Output

```
status: approved | rejected | pending
reviewer: <human>
comments: ...
```
