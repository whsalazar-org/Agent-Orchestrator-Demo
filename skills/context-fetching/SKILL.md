---
name: context-fetching
description: Use at the start of a change request to gather the code, docs and history needed to understand the current behaviour.
---

# Context Fetching

## Checklist

1. **Request** — the issue, its comments and any linked discussion.
2. **Code** — the entry points, the modules that own the behaviour, and their tests.
3. **Conventions** — README, contributing guide, lint/build/test configuration.
4. **History** — recent commits and PRs touching the same files, to avoid re-litigating
   decisions that were already made.
5. **Runtime** — logs, dashboards or CI runs when the request describes a failure.

## Rules

- Cite every source as `path:line` or a URL. Uncited context is an assumption.
- Prefer reading the code over trusting documentation that may be stale.
- Stop collecting when new sources stop changing your understanding.

## Output

A context pack: sources consulted, current behaviour, constraints, and the gaps you
could not close.
