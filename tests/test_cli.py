import json

from orchestrator.cli import main


def test_cli_happy_path_exits_zero(capsys):
    assert main(["add a demo feature"]) == 0
    out = capsys.readouterr().out
    assert "run status: completed" in out
    assert "deployment" in out


def test_cli_blocks_on_pending_review_with_exit_code_two(capsys):
    assert main(["add a demo feature", "--review", "pending"]) == 2
    assert "stopped at: review" in capsys.readouterr().out


def test_cli_fails_when_retries_are_exhausted(capsys):
    assert main(["add a demo feature", "--failing-test-runs", "3"]) == 1
    assert "stopped at: testing" in capsys.readouterr().out


def test_cli_json_output_is_machine_readable(capsys):
    assert main(["add a demo feature", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert [event["stage"] for event in payload["events"]][0] == "analysis"
    assert "deployment_record" in payload["artifacts"]
