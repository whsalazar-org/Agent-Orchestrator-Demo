"""Command line entry point: ``python -m orchestrator``."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Sequence

from .handlers import DemoScenario, demo_handlers
from .pipeline import Orchestrator, RunResult, RunStatus

EXIT_CODES = {RunStatus.COMPLETED: 0, RunStatus.BLOCKED: 2, RunStatus.FAILED: 1}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="Run the demo SDLC pipeline: analysis -> planning -> coding -> "
        "testing -> human review gate -> deployment.",
    )
    parser.add_argument("request", help="the change request to run through the pipeline")
    parser.add_argument(
        "--review",
        choices=("approved", "rejected", "pending"),
        default="approved",
        help="decision the human reviewer records at the gate (default: approved)",
    )
    parser.add_argument(
        "--failing-test-runs",
        type=int,
        default=0,
        help="number of testing attempts that fail before the suite goes green",
    )
    parser.add_argument(
        "--max-test-retries",
        type=int,
        default=1,
        help="how often a failing test report may be sent back to the coding agent",
    )
    parser.add_argument(
        "--deployment-fails",
        action="store_true",
        help="make the post-deploy health check fail so the change is rolled back",
    )
    parser.add_argument("--json", action="store_true", help="print the run result as JSON")
    return parser


def format_result(result: RunResult) -> str:
    lines = [f"run status: {result.status.value}"]
    for event in result.events:
        suffix = f" [{', '.join(event.artifacts)}]" if event.artifacts else ""
        lines.append(
            f"  {event.stage:<10} attempt {event.attempt}  {event.status.value:<9} "
            f"{event.summary}{suffix}"
        )
    if result.stopped_at:
        lines.append(f"stopped at: {result.stopped_at} ({result.reason})")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    scenario = DemoScenario(
        failing_test_runs=args.failing_test_runs,
        review_decision=args.review,
        deployment_fails=args.deployment_fails,
    )
    orchestrator = Orchestrator(
        handlers=demo_handlers(scenario),
        max_test_retries=args.max_test_retries,
    )
    result = orchestrator.run({"title": args.request})

    if args.json:
        print(
            json.dumps(
                {
                    "status": result.status.value,
                    "stopped_at": result.stopped_at,
                    "reason": result.reason,
                    "events": [
                        {**asdict(event), "status": event.status.value, "artifacts": list(event.artifacts)}
                        for event in result.events
                    ],
                    "artifacts": result.artifacts,
                },
                indent=2,
            )
        )
    else:
        print(format_result(result))

    return EXIT_CODES[result.status]


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
