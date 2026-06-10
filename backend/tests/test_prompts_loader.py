"""Prompt loader tests."""

from backend.prompts_loader import PROMPTS_ROOT, load_prompt_file


def test_prompts_root_points_at_repo_prompts_dir() -> None:
    assert PROMPTS_ROOT.name == "prompts"
    assert (PROMPTS_ROOT / "focus" / "system.md").exists()


def test_load_focus_system_prompt() -> None:
    content = load_prompt_file("focus", "system.md")
    assert "# Focus Agent System Prompt" in content
    assert "**Version:** 2.0.0" in content
    assert "## Identity" in content
    assert "You are the **Focus Agent**" in content
