"""Load externalized agent prompts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROMPTS_ROOT = Path(__file__).resolve().parents[1] / "prompts"

V2_STATIC_FILES = (
    "system.md",
    "context.md",
    "instructions.md",
    "examples.md",
    "output-schema.md",
    "tools.md",
    "reasoning.md",
    "guardrails.md",
    "input-security.md",
    "quality-checklist.md",
)

LEGACY_STATIC_FILES = (
    "system.md",
    "skills.md",
    "tools.md",
    "guardrails.md",
    "input-security.md",
)


@dataclass(frozen=True)
class CachedPromptBlock:
    """One static prompt section eligible for provider-side caching."""

    name: str
    content: str
    cache_control: bool = True


@dataclass(frozen=True)
class CachedPromptAssembly:
    """Ordered static prompt blocks for an agent."""

    agent_id: str
    blocks: tuple[CachedPromptBlock, ...]

    @property
    def total_chars(self) -> int:
        return sum(len(block.content) for block in self.blocks)

    @property
    def estimated_tokens(self) -> int:
        return max(self.total_chars // 4, 1)

    def to_openai_system_content(self) -> str:
        """Concatenate static blocks — stable prefix for OpenAI auto-cache."""
        return "\n\n".join(block.content.strip() for block in self.blocks if block.content.strip())

    def to_claude_system_blocks(self) -> list[dict[str, Any]]:
        """Structured system blocks with cache_control for Anthropic models."""
        blocks: list[dict[str, Any]] = []
        for block in self.blocks:
            text = block.content.strip()
            if not text:
                continue
            entry: dict[str, Any] = {"type": "text", "text": text}
            if block.cache_control:
                entry["cache_control"] = {"type": "ephemeral"}
            blocks.append(entry)
        return blocks


def load_prompt_file(agent_id: str, filename: str) -> str:
    """Load a prompt file for an agent."""
    path = PROMPTS_ROOT / agent_id / filename
    if not path.exists():
        msg = f"Prompt file not found: {path}"
        raise FileNotFoundError(msg)
    return path.read_text(encoding="utf-8")


def _static_files_for_agent(agent_id: str) -> tuple[str, ...]:
    agent_dir = PROMPTS_ROOT / agent_id
    if (agent_dir / "instructions.md").exists():
        return V2_STATIC_FILES
    return LEGACY_STATIC_FILES


def build_agent_system_prompt(agent_id: str) -> str:
    """Combine legacy system, skills, and guardrails for LLM calls."""
    system = load_prompt_file(agent_id, "system.md")
    skills = load_prompt_file(agent_id, "skills.md")
    guardrails = load_prompt_file(agent_id, "guardrails.md")
    return f"{system.strip()}\n\n{skills.strip()}\n\n{guardrails.strip()}"


def build_cached_prompt_assembly(agent_id: str) -> CachedPromptAssembly:
    """Build ordered static prompt blocks for provider-side caching."""
    blocks: list[CachedPromptBlock] = []
    for filename in _static_files_for_agent(agent_id):
        path = PROMPTS_ROOT / agent_id / filename
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        block_name = filename.removesuffix(".md")
        blocks.append(
            CachedPromptBlock(
                name=block_name,
                content=content,
                cache_control=True,
            ),
        )
    if not blocks:
        msg = f"No prompt files found for agent: {agent_id}"
        raise FileNotFoundError(msg)
    return CachedPromptAssembly(agent_id=agent_id, blocks=tuple(blocks))
