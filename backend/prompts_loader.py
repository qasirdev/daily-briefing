"""Load externalized agent prompts."""

from pathlib import Path

PROMPTS_ROOT = Path(__file__).resolve().parents[1] / "prompts"


def load_prompt_file(agent_id: str, filename: str) -> str:
    """Load a prompt file for an agent."""
    path = PROMPTS_ROOT / agent_id / filename
    if not path.exists():
        msg = f"Prompt file not found: {path}"
        raise FileNotFoundError(msg)
    return path.read_text(encoding="utf-8")


def build_agent_system_prompt(agent_id: str) -> str:
    """Combine system, skills, and guardrails for LLM calls."""
    system = load_prompt_file(agent_id, "system.md")
    skills = load_prompt_file(agent_id, "skills.md")
    guardrails = load_prompt_file(agent_id, "guardrails.md")
    return f"{system.strip()}\n\n{skills.strip()}\n\n{guardrails.strip()}"
