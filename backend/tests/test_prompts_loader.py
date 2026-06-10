"""Prompt loader tests."""

import pytest

from backend.prompts_loader import (
    PROMPTS_ROOT,
    build_agent_system_prompt,
    build_cached_prompt_assembly,
    load_prompt_file,
)

LLM_AGENT_DIRS = ("focus", "critic", "verification", "adversarial")


def test_prompts_root_points_at_repo_prompts_dir() -> None:
    assert PROMPTS_ROOT.name == "prompts"
    assert (PROMPTS_ROOT / "focus" / "system.md").exists()


def test_load_focus_system_prompt() -> None:
    content = load_prompt_file("focus", "system.md")
    assert "# Focus Agent System Prompt" in content
    assert "**Version:** 2.0.0" in content
    assert "## Identity" in content
    assert "You are the **Focus Agent**" in content


@pytest.mark.parametrize("agent_id", LLM_AGENT_DIRS)
def test_build_agent_system_prompt_includes_skills(agent_id: str) -> None:
    prompt = build_agent_system_prompt(agent_id)
    assert "<skills>" in prompt
    assert "guardrails" in prompt.lower() or "Guardrails" in prompt


@pytest.mark.parametrize("agent_id", LLM_AGENT_DIRS)
def test_cached_assembly_loads_for_all_llm_agents(agent_id: str) -> None:
    assembly = build_cached_prompt_assembly(agent_id)
    assert assembly.estimated_tokens >= 1
    assert assembly.blocks[0].name == "system"
