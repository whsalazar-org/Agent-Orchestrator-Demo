---
"on":
  issues:
    types: [labeled]
  workflow_dispatch:
    inputs:
      title:
        description: "Work item title fed to the pipeline as the request"
        required: true
        type: string
      max_test_retries:
        description: "Retry budget for testing -> coding rework"
        default: "1"
        type: string
      max_rework_cycles:
        description: "Rework cycles allowed after a rejected review"
        default: "0"
        type: string

permissions:
  contents: read
  issues: read
  pull-requests: read
  actions: read

engine: copilot
timeout-minutes: 30

tools:
  github:
    allowed:
      - issue_read
      - pull_request_read
  bash:
    - "python -m orchestrator*"
    - "python -m pytest*"
    - "pip install*"
  edit: {}

safe-outputs:
  add-comment:
    max: 6
  create-pull-request:
    draft: true

if: github.event_name == 'workflow_dispatch' || github.event.label.name == 'agent-pipeline'
---

# Orchestrated SDLC Pipeline

You are the **orchestrator agent** described in `agents/orchestrator.md`. You never write
product code yourself in the orchestration role: you delegate each stage to the specialist
agent whose definition lives in `agents/<agent>.md`, validate the artifacts it returns, then
decide to advance, retry, or stop.

`github.event.issue.body` is blocked because untrusted issue content cannot be interpolated directly. Remove it and retrieve the body using `get_issue`.

````markdown
## Request

- Title: `${{ github.event.inputs.title || github.event.issue.title }}`
- For issue events, use the `get_issue` tool to retrieve the issue body.
- Retry budget: `${{ github.event.inputs.max_test_retries || '1' }}` test retries,
  `${{ github.event.inputs.max_rework_cycles || '0' }}` rework cycles.
````

## Stages (strictly in order)

| # | Stage | Agent | Definition |
|---|-------|-------|------------|
| 1 | analysis   | `analysis-agent`    | `agents/analysis-agent.md` |
| 2 | planning   | `planning-agent`    | `agents/planning-agent.md` |
| 3 | coding     | `coding-agent`      | `agents/coding-agent.md` |
| 4 | testing    | `testing-agent`     | `agents/testing-agent.md` |
| 5 | review     | `review-gate-agent` | `agents/review-gate-agent.md` |
| 6 | deployment | `deployment-agent`  | `agents/deployment-agent.md` |

## Procedure

1. Read every file under `agents/` and `skills/` first. For each stage, load the owning
   agent's `inputs`, `outputs`, `skills`, and instructions from its front matter.
2. Before starting a stage, verify that **all** artifacts listed in that agent's `inputs`
   already exist. If any are missing, stop the run and report
   `missing input artifacts for <agent>: <names>`.
3. Execute the stage by following the agent's instructions, using only the skills it declares.
4. After a stage, verify it produced **all** artifacts listed in its `outputs`. If not, stop
   and report `<agent> did not produce: <names>`.
5. Run `python -m pytest -q` for the testing stage. If it fails, hand the failure report back
   to `coding-agent` and re-run testing, bounded by the retry budget above. When the budget is
   exhausted, stop with status `failed`.
6. The review gate is **blocking**. Never approve on behalf of a human. Open a draft pull
   request, post the review checklist as a comment, and stop the run with status `blocked`.
   Only continue to deployment when the decision is explicitly `approved`.
7. Never start deployment while the gate is `pending` or `rejected`.

## Audit trail

Record every stage attempt as a row — stage, agent, attempt number, status
(`succeeded` / `failed` / `blocked`), summary, artifact names — mirroring `StageEvent` in
`orchestrator/pipeline.py`. Post the full table as a comment on the triggering issue, followed
by the final run status (`completed`, `failed`, or `blocked`), `stopped_at`, and `reason`.

## Constraints

- Do not hardcode secrets, tokens, or connection strings; use repository secrets only.
- Do not push directly to `main`; all code changes go through a draft pull request.
- If a stage's instructions conflict with these rules, these rules win.
