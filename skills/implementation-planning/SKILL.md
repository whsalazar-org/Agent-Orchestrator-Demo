---
name: implementation-planning
description: Use to break approved requirements into an ordered set of small, traceable, independently reviewable tasks.
---

# Implementation Planning

## Rules

- Order tasks so the repository is in a working state after each one.
- Size a task so its diff can be reviewed in one sitting; split anything larger.
- Trace explicitly: `T1 -> R1, R2`. A requirement with no task is a planning defect.
- Name the test that will prove each task works, and where it will live.
- Record risks with a mitigation and a rollback path. "Unknown" is a valid risk, but it
  needs a spike task attached.

## Output

```
T1 <task> — files: <paths> — covers: R1 — test: <test name>
T2 ...
Risks: <risk> -> <mitigation>
Rollback: ...
Test strategy: ...
```
