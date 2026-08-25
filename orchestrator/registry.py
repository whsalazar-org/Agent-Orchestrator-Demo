"""Loading of the agent and skill definitions stored as markdown files.

Definitions use a small YAML-like front matter block (``key: value`` pairs, with
comma separated lists) so the repository stays dependency free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / "agents"
SKILLS_DIR = REPO_ROOT / "skills"

_LIST_FIELDS = ("skills", "inputs", "outputs")


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split a markdown document into its front matter mapping and its body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("document does not start with a '---' front matter block")

    try:
        end = lines.index("---", 1)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError("front matter block is not terminated by '---'") from exc

    meta: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"invalid front matter line: {line!r}")
        meta[key.strip()] = value.strip()

    return meta, "\n".join(lines[end + 1 :]).strip()


def _split_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class AgentDefinition:
    """A specialist agent that owns one stage of the pipeline."""

    name: str
    stage: str
    description: str
    skills: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    instructions: str = ""

    @classmethod
    def from_file(cls, path: Path) -> "AgentDefinition":
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        missing = {"name", "stage", "description"} - meta.keys()
        if missing:
            raise ValueError(f"{path.name}: missing front matter keys: {sorted(missing)}")
        return cls(
            name=meta["name"],
            stage=meta["stage"],
            description=meta["description"],
            skills=_split_list(meta.get("skills", "")),
            inputs=_split_list(meta.get("inputs", "")),
            outputs=_split_list(meta.get("outputs", "")),
            instructions=body,
        )


@dataclass(frozen=True)
class SkillDefinition:
    """A reusable procedure that agents apply."""

    name: str
    description: str
    instructions: str = ""

    @classmethod
    def from_file(cls, path: Path) -> "SkillDefinition":
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        missing = {"name", "description"} - meta.keys()
        if missing:
            raise ValueError(f"{path.parent.name}: missing front matter keys: {sorted(missing)}")
        return cls(name=meta["name"], description=meta["description"], instructions=body)


def load_agents(directory: Path = AGENTS_DIR) -> dict[str, AgentDefinition]:
    """Load every agent definition in ``directory``, keyed by agent name."""
    agents: dict[str, AgentDefinition] = {}
    for path in sorted(directory.glob("*.md")):
        agent = AgentDefinition.from_file(path)
        agents[agent.name] = agent
    return agents


def load_skills(directory: Path = SKILLS_DIR) -> dict[str, SkillDefinition]:
    """Load every ``<skill>/SKILL.md`` in ``directory``, keyed by skill name."""
    skills: dict[str, SkillDefinition] = {}
    for path in sorted(directory.glob("*/SKILL.md")):
        skill = SkillDefinition.from_file(path)
        skills[skill.name] = skill
    return skills
