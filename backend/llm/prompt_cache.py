"""Prompt caching utilities for Claude cache_control and OpenAI auto-cache."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.llm.router import LLMRouter

import structlog

from backend.prompts_loader import build_cached_prompt_assembly
from backend.settings import Settings

logger = structlog.get_logger()

OPENAI_AUTO_CACHE_MIN_TOKENS = 1024
WARM_USER_CONTENT = "Cache warm — respond with the single word OK."
WARM_TRACE_ID = "warm" + ("0" * 28)


def is_claude_model(model: str) -> bool:
    """Return True when the model identifier targets Anthropic Claude."""
    normalized = model.lower()
    return "claude" in normalized or "anthropic" in normalized


def is_openai_model(model: str) -> bool:
    """Return True when the model identifier targets OpenAI."""
    normalized = model.lower()
    return normalized.startswith("openai/") or "gpt" in normalized


def infer_cache_provider(model: str) -> str:
    if is_claude_model(model):
        return "anthropic"
    if is_openai_model(model):
        return "openai"
    return "openrouter"


def resolve_model_name(llm: LLMRouter) -> str:
    """Resolve model identifier from router or settings fallback."""
    model = getattr(llm, "primary_model", None)
    if isinstance(model, str) and model:
        return model
    from backend.settings import get_settings

    return get_settings().llm_primary_model


def openai_cache_eligible(agent_id: str) -> bool:
    """Return True when static prompt size meets OpenAI auto-cache threshold."""
    return build_cached_prompt_assembly(agent_id).estimated_tokens >= OPENAI_AUTO_CACHE_MIN_TOKENS


def build_llm_messages(
    agent_id: str,
    user_content: str,
    *,
    model: str,
    enable_caching: bool = True,
) -> list[dict[str, Any]]:
    """Build LLM messages with static cacheable content before dynamic user input."""
    assembly = build_cached_prompt_assembly(agent_id)
    if enable_caching and is_claude_model(model):
        return [
            {"role": "system", "content": assembly.to_claude_system_blocks()},
            {"role": "user", "content": user_content},
        ]
    return [
        {"role": "system", "content": assembly.to_openai_system_content()},
        {"role": "user", "content": user_content},
    ]


class PromptCacheWarmer:
    """Warm provider prompt caches for frequently-used agents."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._agent_ids = settings.prompt_cache_warm_agent_list
        self._task: asyncio.Task[None] | None = None

    async def warm_agent(self, llm: LLMRouter, agent_id: str) -> None:
        """Send a minimal request to populate the provider cache for one agent."""
        from backend.metrics import set_cache_size_bytes

        model = llm.primary_model
        messages = build_llm_messages(
            agent_id,
            WARM_USER_CONTENT,
            model=model,
            enable_caching=self._settings.enable_prompt_caching,
        )
        assembly = build_cached_prompt_assembly(agent_id)
        set_cache_size_bytes(
            provider=infer_cache_provider(model),
            size_bytes=assembly.total_chars,
        )
        await llm.generate(
            messages=messages,
            trace_id=WARM_TRACE_ID,
            output_budget=16,
            agent_id=agent_id,
            data_classification="internal",
        )
        logger.info(
            "prompt_cache_warmed",
            agent_id=agent_id,
            model=model,
            estimated_tokens=assembly.estimated_tokens,
        )

    async def warm_all(self, llm: LLMRouter) -> None:
        """Warm caches for all configured agents sequentially."""
        for agent_id in self._agent_ids:
            try:
                await self.warm_agent(llm, agent_id)
            except Exception as exc:
                logger.warning(
                    "prompt_cache_warm_agent_failed",
                    agent_id=agent_id,
                    error=str(exc),
                )

    def start_background_loop(self, llm: LLMRouter) -> None:
        """Start periodic cache warming in the background."""
        if self._task is not None and not self._task.done():
            return

        async def _loop() -> None:
            interval = self._settings.prompt_cache_warm_interval_seconds
            while True:
                await self.warm_all(llm)
                await asyncio.sleep(interval)

        self._task = asyncio.create_task(_loop())

    async def stop(self) -> None:
        """Cancel the background warming loop."""
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
