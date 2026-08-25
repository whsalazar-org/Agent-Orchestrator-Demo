import pytest

from orchestrator.handlers import DemoScenario, demo_handlers
from orchestrator.pipeline import (
    Orchestrator,
    PipelineError,
    RunStatus,
    StageResult,
    StageStatus,
)

REQUEST = {"title": "add a demo feature"}


def run(scenario: DemoScenario | None = None, **kwargs):
    orchestrator = Orchestrator(handlers=demo_handlers(scenario), **kwargs)
    return orchestrator.run(REQUEST)


def test_happy_path_runs_every_stage_in_order():
    result = run()
    assert result.status is RunStatus.COMPLETED
    assert result.completed_stages == [
        "analysis",
        "planning",
        "coding",
        "testing",
        "review",
        "deployment",
    ]
    assert result.artifacts["deployment_record"]["rolled_back"] is False


def test_failing_tests_are_sent_back_to_the_coding_agent():
    result = run(DemoScenario(failing_test_runs=1))
    assert result.status is RunStatus.COMPLETED
    assert [e.stage for e in result.events] == [
        "analysis",
        "planning",
        "coding",
        "testing",
        "coding",
        "testing",
        "review",
        "deployment",
    ]
    assert result.artifacts["changeset"]["rework"] is True


def test_retry_budget_is_bounded():
    result = run(DemoScenario(failing_test_runs=5), max_test_retries=1)
    assert result.status is RunStatus.FAILED
    assert result.stopped_at == "testing"
    assert [e.stage for e in result.events].count("testing") == 2
    assert "deployment" not in result.completed_stages


def test_pending_review_blocks_the_pipeline_before_deployment():
    result = run(DemoScenario(review_decision="pending"))
    assert result.status is RunStatus.BLOCKED
    assert result.stopped_at == "review"
    assert "deployment" not in [e.stage for e in result.events]
    assert "deployment_record" not in result.artifacts


def test_rejected_review_stops_the_run_by_default():
    result = run(DemoScenario(review_decision="rejected"))
    assert result.status is RunStatus.FAILED
    assert result.stopped_at == "review"
    assert "deployment" not in [e.stage for e in result.events]


def test_rejected_review_can_be_reworked_when_allowed():
    scenario = DemoScenario(review_decision="rejected")

    handlers = demo_handlers(scenario)
    review = handlers["review"]
    state = {"calls": 0}

    def review_once_then_approve(agent, artifacts):
        state["calls"] += 1
        if state["calls"] > 1:
            scenario.review_decision = "approved"
        return review(agent, artifacts)

    handlers["review"] = review_once_then_approve
    result = Orchestrator(handlers=handlers, max_rework_cycles=1).run(REQUEST)

    assert result.status is RunStatus.COMPLETED
    assert [e.stage for e in result.events].count("review") == 2
    assert [e.stage for e in result.events].count("coding") == 2


def test_deployment_refuses_to_run_without_approval():
    handlers = demo_handlers(DemoScenario(review_decision="rejected"))
    deployment = handlers["deployment"]
    result = deployment(
        Orchestrator(handlers=handlers).agents["deployment-agent"],
        {"review_decision": {"status": "rejected"}},
    )
    assert result.status is StageStatus.FAILED
    assert "approved review" in result.summary


def test_failed_health_check_rolls_back():
    result = run(DemoScenario(deployment_fails=True))
    assert result.status is RunStatus.FAILED
    assert result.stopped_at == "deployment"
    assert result.artifacts["deployment_record"]["rolled_back"] is True


def test_missing_input_artifact_fails_the_run():
    handlers = demo_handlers()
    handlers["analysis"] = lambda agent, artifacts: StageResult(StageStatus.SUCCEEDED, {})
    result = Orchestrator(handlers=handlers).run(REQUEST)
    assert result.status is RunStatus.FAILED
    assert result.stopped_at == "analysis"
    assert "did not produce" in result.reason


def test_stage_that_skips_an_output_is_detected_downstream():
    handlers = demo_handlers()
    handlers["analysis"] = lambda agent, artifacts: StageResult(
        StageStatus.SUCCEEDED, {"context_pack": {}, "requirements": []}
    )
    handlers["planning"] = lambda agent, artifacts: StageResult(StageStatus.SUCCEEDED, {"plan": {}})
    handlers["coding"] = lambda agent, artifacts: StageResult(StageStatus.SUCCEEDED, {})
    result = Orchestrator(handlers=handlers).run(REQUEST)
    assert result.status is RunStatus.FAILED
    assert result.stopped_at == "coding"


def test_missing_handler_is_rejected():
    handlers = demo_handlers()
    del handlers["testing"]
    with pytest.raises(PipelineError, match="testing"):
        Orchestrator(handlers=handlers)


def test_events_record_each_attempt_and_artifacts():
    result = run()
    analysis = result.events[0]
    assert (analysis.stage, analysis.agent, analysis.attempt) == ("analysis", "analysis-agent", 1)
    assert set(analysis.artifacts) == {"context_pack", "requirements"}
