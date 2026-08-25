from pathlib import Path

import pytest

from orchestrator.registry import (
    AgentDefinition,
    load_agents,
    load_skills,
    parse_front_matter,
)
from orchestrator.pipeline import STAGES


def test_parse_front_matter_splits_metadata_and_body():
    meta, body = parse_front_matter("---\nname: demo\nskills: a, b\n---\n\n# Body\ntext\n")
    assert meta == {"name": "demo", "skills": "a, b"}
    assert body == "# Body\ntext"


def test_parse_front_matter_rejects_document_without_block():
    with pytest.raises(ValueError):
        parse_front_matter("# no front matter\n")


def test_every_stage_has_an_agent_definition():
    agents = load_agents()
    for stage in STAGES:
        agent = agents[stage.agent]
        assert agent.stage == stage.name
        assert agent.description


def test_orchestrator_agent_is_defined():
    assert "orchestrator" in load_agents()


def test_agent_skills_resolve_to_existing_skills():
    skills = load_skills()
    for agent in load_agents().values():
        for skill in agent.skills:
            assert skill in skills, f"{agent.name} references unknown skill {skill}"


def test_stage_inputs_are_produced_by_earlier_stages():
    agents = load_agents()
    available = {"request"}
    for stage in STAGES:
        agent = agents[stage.agent]
        assert set(agent.inputs) <= available, f"{agent.name} needs artifacts nobody produced"
        available.update(agent.outputs)


def test_definitions_are_loaded_from_files(tmp_path: Path):
    path = tmp_path / "sample.md"
    path.write_text(
        "---\nname: sample\nstage: analysis\ndescription: d\n"
        "skills: s1\ninputs: a\noutputs: b\n---\nbody\n",
        encoding="utf-8",
    )
    agent = AgentDefinition.from_file(path)
    assert (agent.skills, agent.inputs, agent.outputs, agent.instructions) == (["s1"], ["a"], ["b"], "body")


def test_missing_front_matter_keys_are_reported(tmp_path: Path):
    path = tmp_path / "broken.md"
    path.write_text("---\nname: broken\n---\nbody\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing front matter keys"):
        AgentDefinition.from_file(path)
