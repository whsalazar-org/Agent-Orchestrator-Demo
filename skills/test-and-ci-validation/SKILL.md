---
name: test-and-ci-validation
description: Use to validate a changeset with the repository's existing lint, build and test commands and to report failures usefully.
---

# Test and CI Validation

## Rules

- Use the commands the repository already defines (CI workflow, package scripts,
  `Makefile`). Do not introduce a new test runner to make a change pass.
- Run targeted tests first, then the full suite once the targeted tests are green.
- A change that only passes because a test was weakened or deleted has failed.
- Confirm the plan's test strategy is covered: new behaviour needs a new test.

## Reporting failures

For each failure report the command, the trimmed error output, the suspected cause and
the file most likely responsible. The coding stage must be able to act on the report
without repeating the investigation.

## Output

```
passed: true|false
checks: [{name, command, status, details}]
```
