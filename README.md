# Agent-Orchestrator-Demo

A sample set of **agents** and **skills** driven by an **orchestrator agent** through a
complete SDLC sequence:

```
Analysis (context fetching & requirements)
      -> Planning
           -> Coding & implementation
                -> Testing & CI validation
                     -> Human review gate
                          -> Deployment & operations
```

## Layout

| Path | What it holds |
| --- | --- |
| `agents/` | One markdown definition per agent (front matter + instructions) |
| `skills/<name>/SKILL.md` | Reusable procedures the agents apply |
| `orchestrator/` | A runnable orchestrator that sequences the stages |
| `tests/` | Tests for the definitions and the orchestration logic |

### Agents

| Agent | Stage | Consumes | Produces |
| --- | --- | --- | --- |
| `orchestrator` | orchestration | — | run log |
| `analysis-agent` | analysis | `request` | `context_pack`, `requirements` |
| `planning-agent` | planning | `context_pack`, `requirements` | `plan` |
| `coding-agent` | coding | `plan` | `changeset` |
| `testing-agent` | testing | `plan`, `changeset` | `test_report` |
| `review-gate-agent` | review | `requirements`, `plan`, `changeset`, `test_report` | `review_decision` |
| `deployment-agent` | deployment | `changeset`, `review_decision` | `deployment_record` |

### Skills

`pipeline-orchestration`, `context-fetching`, `requirements-analysis`,
`implementation-planning`, `code-implementation`, `test-and-ci-validation`,
`human-review-gate`, `deployment-and-operations`.

Each agent declares the skills it uses in its front matter, so a skill can be shared by
several agents and updated in one place.

## Running the demo

The demo handlers stand in for real agent invocations: they emit the artifacts each
agent declares, which lets you exercise the orchestration rules without calling a model.

```console
$ python -m orchestrator "Add rate limiting to the API"
run status: completed
  analysis   attempt 1  succeeded analysis-agent: gathered context and derived 1 requirement [context_pack, requirements]
  planning   attempt 1  succeeded planning-agent: planned 1 task(s) [plan]
  coding     attempt 1  succeeded coding-agent: implemented 1 task(s) [changeset]
  testing    attempt 1  succeeded testing-agent: all checks passed [test_report]
  review     attempt 1  succeeded review-gate-agent: review approved [review_decision]
  deployment attempt 1  succeeded deployment-agent: deployed and healthy [deployment_record]
```

Other paths through the pipeline:

```console
$ python -m orchestrator "Add rate limiting" --failing-test-runs 1   # testing -> coding -> testing
$ python -m orchestrator "Add rate limiting" --review pending        # blocked at the human gate
$ python -m orchestrator "Add rate limiting" --review rejected       # stopped, nothing deployed
$ python -m orchestrator "Add rate limiting" --json                  # machine readable run log
```

Exit codes: `0` completed, `1` failed, `2` blocked on the human gate.

## Orchestration rules

- Stages run strictly in order, and a stage only starts once all of the input artifacts
  it declares exist.
- A failing `test_report` is routed back to `coding-agent` and re-validated, bounded by
  `--max-test-retries`.
- The human review gate is blocking: `pending` stops the run, and `deployment-agent`
  refuses to run unless the decision is `approved`.
- Every stage attempt is appended to an audit trail (stage, agent, attempt, status,
  artifacts).

## Wiring in real agents

Replace the demo handlers with calls to your agent runtime; the orchestrator only needs
a callable per stage:

```python
from orchestrator import Orchestrator, StageResult, StageStatus

def analysis(agent, artifacts):
    response = my_agent_runtime.invoke(agent.name, agent.instructions, artifacts)
    return StageResult(StageStatus.SUCCEEDED, response.artifacts, response.summary)

Orchestrator(handlers={"analysis": analysis, ...}).run({"title": "Add rate limiting"})
```

## Tests

```console
$ python -m pip install pytest
$ python -m pytest
```
