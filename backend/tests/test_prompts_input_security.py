"""v2.0.0 input-security.md coverage for all agent prompt packs."""

from __future__ import annotations

import pytest

from backend.prompts_loader import PROMPTS_ROOT, build_cached_prompt_assembly

PRODUCTION_AGENT_DIRS = (
    "task",
    "calendar",
    "focus",
    "critic",
    "verification",
    "adversarial",
    "orchestrator",
    "security",
)

V2_REQUIRED_FILES = (
    "system.md",
    "context.md",
    "instructions.md",
    "examples.md",
    "output-schema.md",
    "tools.md",
    "skills.md",
    "reasoning.md",
    "guardrails.md",
    "input-security.md",
    "quality-checklist.md",
    "CHANGELOG.md",
    "CONTRACT.md",
)

LLM_AGENT_DIRS = ("focus", "critic", "verification", "adversarial")

EXTERNAL_CONTENT_MARKER = "<<<EXTERNAL_CONTENT>>>"


@pytest.mark.parametrize("agent_id", PRODUCTION_AGENT_DIRS)
def test_input_security_file_exists(agent_id: str) -> None:
    path = PROMPTS_ROOT / agent_id / "input-security.md"
    assert path.is_file(), f"Missing input-security.md for {agent_id}"
    text = path.read_text(encoding="utf-8")
    assert EXTERNAL_CONTENT_MARKER in text
    assert "**Version:** 2.0.0" in text


@pytest.mark.parametrize("agent_id", LLM_AGENT_DIRS)
def test_cached_assembly_includes_input_security(agent_id: str) -> None:
    assembly = build_cached_prompt_assembly(agent_id)
    block_names = [block.name for block in assembly.blocks]
    assert "input-security" in block_names
    assert block_names.index("input-security") > block_names.index("guardrails")


@pytest.mark.parametrize("agent_id", LLM_AGENT_DIRS)
def test_cached_assembly_includes_v2_schema_and_quality(agent_id: str) -> None:
    """v2.0.0 requires output-schema and quality-checklist in static prompt assembly."""
    assembly = build_cached_prompt_assembly(agent_id)
    block_names = [block.name for block in assembly.blocks]
    assert "output-schema" in block_names
    assert "quality-checklist" in block_names
    assert block_names.index("output-schema") > block_names.index("examples")
    assert block_names.index("quality-checklist") > block_names.index("input-security")


def test_focus_input_security_block_is_cacheable() -> None:
    assembly = build_cached_prompt_assembly("focus")
    security_block = next(block for block in assembly.blocks if block.name == "input-security")
    assert security_block.cache_control is True
    assert "Spotlighting" in security_block.content


@pytest.mark.parametrize("agent_id", PRODUCTION_AGENT_DIRS)
def test_v2_prompt_pack_has_required_files(agent_id: str) -> None:
    agent_dir = PROMPTS_ROOT / agent_id
    for filename in V2_REQUIRED_FILES:
        assert (agent_dir / filename).is_file(), f"{agent_id} missing {filename}"


@pytest.mark.parametrize("agent_id", PRODUCTION_AGENT_DIRS)
def test_contract_version_is_v2(agent_id: str) -> None:
    contract = (PROMPTS_ROOT / agent_id / "CONTRACT.md").read_text(encoding="utf-8")
    assert "v2.0.0" in contract, f"{agent_id} CONTRACT.md must declare v2.0.0"
