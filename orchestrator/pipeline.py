"""The orchestrator state machine that drives the SDLC stages in order."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping

from .registry import AgentDefinition, load_agents


class StageStatus(str, Enum):
    """Outcome of a single stage attempt."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    #: A gate is waiting on someone outside the pipeline (e.g. a human reviewer).
    BLOCKED = "blocked"


class RunStatus(str, Enum):
    """Outcome of a whole pipeline run."""

    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class Stage:
    """A pipeline stage and the agent that owns it."""

    name: str
    agent: str
    description: str


#: The SDLC sequence this demo implements.
STAGES: tuple[Stage, ...] = (
    Stage("analysis", "analysis-agent", "Context fetching & requirements"),
    Stage("planning", "planning-agent", "Planning"),
    Stage("coding", "coding-agent", "Coding & implementation"),
    Stage("testing", "testing-agent", "Testing & CI validation"),
    Stage("review", "review-gate-agent", "Human review gate"),
    Stage("deployment", "deployment-agent", "Deployment & operations"),
)


@dataclass(frozen=True)
class StageResult:
    """What an agent hands back to the orchestrator."""

    status: StageStatus
    artifacts: Mapping[str, object] = field(default_factory=dict)
    summary: str = ""


@dataclass(frozen=True)
class StageEvent:
    """One audited stage attempt."""

    stage: str
    agent: str
    attempt: int
    status: StageStatus
    summary: str
    artifacts: tuple[str, ...] = ()


@dataclass
class RunResult:
    """The result of a pipeline run, including its audit trail."""

    status: RunStatus
    artifacts: dict[str, object]
    events: list[StageEvent]
    stopped_at: str | None = None
    reason: str = ""

    @property
    def completed_stages(self) -> list[str]:
        return [e.stage for e in self.events if e.status is StageStatus.SUCCEEDED]


#: A stage handler receives the artifacts produced so far and returns a result.
StageHandler = Callable[[AgentDefinition, Mapping[str, object]], StageResult]


class PipelineError(RuntimeError):
    """Raised when the pipeline itself is misconfigured."""


class Orchestrator:
    """Runs the SDLC stages in order, honouring retries and the human gate."""

    def __init__(
        self,
        handlers: Mapping[str, StageHandler],
        agents: Mapping[str, AgentDefinition] | None = None,
        stages: tuple[Stage, ...] = STAGES,
        max_test_retries: int = 1,
        max_rework_cycles: int = 0,
    ) -> None:
        self.stages = stages
        self.agents = dict(agents) if agents is not None else load_agents()
        self.handlers = dict(handlers)
        self.max_test_retries = max_test_retries
        self.max_rework_cycles = max_rework_cycles

        for stage in self.stages:
            if stage.agent not in self.agents:
                raise PipelineError(f"no definition found for agent {stage.agent!r}")
            if stage.name not in self.handlers:
                raise PipelineError(f"no handler registered for stage {stage.name!r}")

    def _stage_index(self, name: str) -> int:
        for index, stage in enumerate(self.stages):
            if stage.name == name:
                return index
        raise PipelineError(f"unknown stage {name!r}")

    def run(self, request: Mapping[str, object]) -> RunResult:
        """Execute the pipeline for ``request`` and return the run result."""
        artifacts: dict[str, object] = {"request": dict(request)}
        events: list[StageEvent] = []
        attempts: dict[str, int] = {}
        test_retries = 0
        rework_cycles = 0

        index = 0
        while index < len(self.stages):
            stage = self.stages[index]
            agent = self.agents[stage.agent]

            missing = [name for name in agent.inputs if name not in artifacts]
            if missing:
                return RunResult(
                    RunStatus.FAILED,
                    artifacts,
                    events,
                    stopped_at=stage.name,
                    reason=f"missing input artifacts for {agent.name}: {', '.join(missing)}",
                )

            attempts[stage.name] = attempts.get(stage.name, 0) + 1
            result = self.handlers[stage.name](agent, artifacts)
            artifacts.update(result.artifacts)
            events.append(
                StageEvent(
                    stage=stage.name,
                    agent=agent.name,
                    attempt=attempts[stage.name],
                    status=result.status,
                    summary=result.summary,
                    artifacts=tuple(result.artifacts),
                )
            )

            if result.status is StageStatus.BLOCKED:
                return RunResult(
                    RunStatus.BLOCKED,
                    artifacts,
                    events,
                    stopped_at=stage.name,
                    reason=result.summary,
                )

            if result.status is StageStatus.FAILED:
                # Failing tests are the one failure the pipeline knows how to fix:
                # send the report back to the coding agent and validate again.
                if stage.name == "testing" and test_retries < self.max_test_retries:
                    test_retries += 1
                    index = self._stage_index("coding")
                    continue
                # A rejected review can be reworked when the run allows it.
                if stage.name == "review" and rework_cycles < self.max_rework_cycles:
                    rework_cycles += 1
                    test_retries = 0
                    index = self._stage_index("coding")
                    continue
                return RunResult(
                    RunStatus.FAILED,
                    artifacts,
                    events,
                    stopped_at=stage.name,
                    reason=result.summary,
                )

            produced = [name for name in agent.outputs if name not in artifacts]
            if produced:
                return RunResult(
                    RunStatus.FAILED,
                    artifacts,
                    events,
                    stopped_at=stage.name,
                    reason=f"{agent.name} did not produce: {', '.join(produced)}",
                )

            index += 1

        return RunResult(RunStatus.COMPLETED, artifacts, events)
