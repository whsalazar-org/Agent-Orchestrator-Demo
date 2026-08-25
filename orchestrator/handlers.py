"""Demo stage handlers.

The handlers stand in for real agent invocations: each one produces the artifacts its
agent declares in ``agents/<agent>.md`` so the orchestration logic (ordering, retries,
the human gate) can be exercised and tested without calling a model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .pipeline import StageHandler, StageResult, StageStatus
from .registry import AgentDefinition


@dataclass
class DemoScenario:
    """Knobs that make the demo run take a different path through the pipeline."""

    #: Number of leading testing attempts that fail before the suite goes green.
    failing_test_runs: int = 0
    #: Decision the human reviewer records: ``approved``, ``rejected`` or ``pending``.
    review_decision: str = "approved"
    reviewer: str = "release-manager"
    review_comments: str = ""
    #: Fail the post-deploy health check and roll back.
    deployment_fails: bool = False

    _test_runs: int = field(default=0, init=False, repr=False)


def _analysis(agent: AgentDefinition, artifacts: Mapping[str, object]) -> StageResult:
    request = artifacts["request"]
    title = request.get("title", "untitled request")
    return StageResult(
        StageStatus.SUCCEEDED,
        {
            "context_pack": {
                "sources": ["README.md", "agents/", "skills/"],
                "current_behaviour": f"no implementation for: {title}",
                "constraints": request.get("constraints", []),
            },
            "requirements": [
                {"id": "R1", "priority": "must", "text": title, "accept_when": "demo run completes"},
            ],
        },
        summary=f"{agent.name}: gathered context and derived 1 requirement",
    )


def _planning(agent: AgentDefinition, artifacts: Mapping[str, object]) -> StageResult:
    requirements = artifacts["requirements"]
    tasks = [
        {"id": f"T{index}", "covers": requirement["id"], "text": f"implement {requirement['text']}"}
        for index, requirement in enumerate(requirements, start=1)
    ]
    return StageResult(
        StageStatus.SUCCEEDED,
        {
            "plan": {
                "tasks": tasks,
                "risks": ["demo only: no production systems are touched"],
                "test_strategy": "unit tests for every task",
            }
        },
        summary=f"{agent.name}: planned {len(tasks)} task(s)",
    )


def _make_coding(scenario: DemoScenario) -> StageHandler:
    def handler(agent: AgentDefinition, artifacts: Mapping[str, object]) -> StageResult:
        plan = artifacts["plan"]
        previous = artifacts.get("test_report")
        reworking = bool(previous) and not previous.get("passed", True)
        return StageResult(
            StageStatus.SUCCEEDED,
            {
                "changeset": {
                    "tasks": [task["id"] for task in plan["tasks"]],
                    "files": ["orchestrator/pipeline.py"],
                    "rework": reworking,
                }
            },
            summary=(
                f"{agent.name}: fixed reported test failures"
                if reworking
                else f"{agent.name}: implemented {len(plan['tasks'])} task(s)"
            ),
        )

    return handler


def _make_testing(scenario: DemoScenario) -> StageHandler:
    def handler(agent: AgentDefinition, artifacts: Mapping[str, object]) -> StageResult:
        scenario._test_runs += 1
        passed = scenario._test_runs > scenario.failing_test_runs
        checks = [
            {
                "name": "pytest",
                "command": "python -m pytest",
                "status": "passed" if passed else "failed",
                "details": "" if passed else "test_pipeline.py::test_demo failed",
            }
        ]
        return StageResult(
            StageStatus.SUCCEEDED if passed else StageStatus.FAILED,
            {"test_report": {"passed": passed, "checks": checks}},
            summary=f"{agent.name}: {'all checks passed' if passed else 'pytest failed'}",
        )

    return handler


def _make_review(scenario: DemoScenario) -> StageHandler:
    status_map = {
        "approved": StageStatus.SUCCEEDED,
        "rejected": StageStatus.FAILED,
        "pending": StageStatus.BLOCKED,
    }

    def handler(agent: AgentDefinition, artifacts: Mapping[str, object]) -> StageResult:
        decision = scenario.review_decision
        if decision not in status_map:
            raise ValueError(f"unknown review decision: {decision!r}")
        return StageResult(
            status_map[decision],
            {
                "review_decision": {
                    "status": decision,
                    "reviewer": scenario.reviewer if decision != "pending" else None,
                    "comments": scenario.review_comments,
                }
            },
            summary=f"{agent.name}: review {decision}",
        )

    return handler


def _make_deployment(scenario: DemoScenario) -> StageHandler:
    def handler(agent: AgentDefinition, artifacts: Mapping[str, object]) -> StageResult:
        decision = artifacts.get("review_decision", {})
        if decision.get("status") != "approved":
            return StageResult(
                StageStatus.FAILED,
                summary=f"{agent.name}: refused to deploy without an approved review",
            )

        healthy = not scenario.deployment_fails
        return StageResult(
            StageStatus.SUCCEEDED if healthy else StageStatus.FAILED,
            {
                "deployment_record": {
                    "environment": "staging",
                    "version": "demo-1",
                    "health_checks": [{"name": "http /healthz", "status": "passed" if healthy else "failed"}],
                    "rolled_back": not healthy,
                    "monitoring": ["https://example.invalid/dashboards/demo"],
                }
            },
            summary=(
                f"{agent.name}: deployed and healthy"
                if healthy
                else f"{agent.name}: health check failed, rolled back"
            ),
        )

    return handler


def demo_handlers(scenario: DemoScenario | None = None) -> dict[str, StageHandler]:
    """Build the stage handlers for a demo run."""
    scenario = scenario or DemoScenario()
    return {
        "analysis": _analysis,
        "planning": _planning,
        "coding": _make_coding(scenario),
        "testing": _make_testing(scenario),
        "review": _make_review(scenario),
        "deployment": _make_deployment(scenario),
    }
