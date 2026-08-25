---
name: deployment-and-operations
description: Use to release an approved change safely and to verify and monitor it after it is live.
---

# Deployment and Operations

## Rules

- Deploy only what a human approved, and deploy the exact artifact that was tested.
- Roll out progressively (canary, then full) and verify health between steps.
- Every deployment needs an automated rollback trigger and a tested rollback path.
- Post-deploy verification is part of the deployment: health endpoint, error rate,
  latency and the SLIs named in the plan.
- Hand over dashboards, alerts and the runbook entry for the change.

## Output

```
environment: <env>
version: <artifact version>
health_checks: [{name, status}]
rolled_back: true|false
monitoring: [<links>]
```
