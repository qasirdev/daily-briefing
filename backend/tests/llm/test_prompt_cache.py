"""Tests for prompt caching (Week 2 Day 1)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.llm.prompt_cache import (
    OPENAI_AUTO_CACHE_MIN_TOKENS,
    build_llm_messages,
    is_claude_model,
    openai_cache_eligible,
)
from backend.llm.router import LLMRouter
from backend.observability.metrics import (
    CACHE_HIT_RATE,
    CACHE_HIT_TOTAL,
    CACHE_MISS_TOTAL,
    record_llm_cache_usage,
)
from backend.prompts_loader import build_cached_prompt_assembly
from backend.settings import Settings


def test_adversarial_cached_prompt_exceeds_openai_threshold() -> None:
    assembly = build_cached_prompt_assembly("adversarial")
    assert assembly.estimated_tokens >= OPENAI_AUTO_CACHE_MIN_TOKENS
    assert openai_cache_eligible("adversarial")


def test_verification_openai_cache_eligible_helper() -> None:
    assert openai_cache_eligible("verification")


def test_focus_cached_prompt_exceeds_openai_threshold() -> None:
    assembly = build_cached_prompt_assembly("focus")
    assert assembly.estimated_tokens >= OPENAI_AUTO_CACHE_MIN_TOKENS


def test_verification_cached_prompt_has_multiple_blocks() -> None:
    assembly = build_cached_prompt_assembly("verification")
    assert len(assembly.blocks) >= 5
    assert assembly.blocks[0].name == "system"


def test_claude_system_blocks_include_cache_control() -> None:
    assembly = build_cached_prompt_assembly("verification")
    blocks = assembly.to_claude_system_blocks()
    assert blocks
    assert all("cache_control" in block for block in blocks)
    assert all(block["cache_control"] == {"type": "ephemeral"} for block in blocks)


def test_build_llm_messages_places_user_content_last() -> None:
    messages = build_llm_messages(
        "focus",
        "dynamic user payload",
        model="openai/gpt-4o-mini",
        enable_caching=True,
    )
    assert len(messages) == 2
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "dynamic user payload"
    assert isinstance(messages[0]["content"], str)


def test_build_llm_messages_uses_claude_blocks_for_anthropic() -> None:
    messages = build_llm_messages(
        "verification",
        "verify this",
        model="anthropic/claude-opus-4",
        enable_caching=True,
    )
    assert isinstance(messages[0]["content"], list)
    assert is_claude_model("anthropic/claude-opus-4")


def test_record_llm_cache_usage_increments_hit_counter() -> None:
    provider = "openai"
    model = "test-cache-hit-model"
    initial_hits = CACHE_HIT_TOTAL.labels(provider=provider, model=model)._value.get()
    record_llm_cache_usage(provider=provider, model=model, cached_tokens=512)
    final_hits = CACHE_HIT_TOTAL.labels(provider=provider, model=model)._value.get()
    assert final_hits == initial_hits + 1


def test_record_llm_cache_usage_increments_miss_counter() -> None:
    provider = "openai"
    model = "test-cache-miss-model"
    initial_misses = CACHE_MISS_TOTAL.labels(provider=provider, model=model)._value.get()
    record_llm_cache_usage(provider=provider, model=model, cached_tokens=0)
    final_misses = CACHE_MISS_TOTAL.labels(provider=provider, model=model)._value.get()
    assert final_misses == initial_misses + 1


def test_record_llm_cache_usage_updates_hit_rate_gauge() -> None:
    provider = "openai"
    model = "test-cache-rate-model"
    record_llm_cache_usage(provider=provider, model=model, cached_tokens=0)
    record_llm_cache_usage(provider=provider, model=model, cached_tokens=100)
    rate = CACHE_HIT_RATE.labels(provider=provider, model=model)._value.get()
    assert rate == 50.0


@pytest.mark.asyncio
async def test_router_records_cache_hits_from_usage_details() -> None:
    settings = Settings(openrouter_api_key="test", enable_prompt_caching=True)
    router = LLMRouter(settings)

    usage = MagicMock()
    usage.total_tokens = 100
    usage.prompt_tokens = 100
    usage.prompt_tokens_details = MagicMock(cached_tokens=80)

    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content='{"ok": true}'))]
    completion.model = "openai/gpt-4o-mini"
    completion.usage = usage

    with patch.object(
        router._primary.chat.completions,
        "create",
        AsyncMock(return_value=completion),
    ):
        await router.generate(
            messages=[{"role": "user", "content": "hello"}],
            trace_id="c" * 32,
            agent_id="focus",
        )

    hits = CACHE_HIT_TOTAL.labels(provider="openai", model="openai/gpt-4o-mini")._value.get()
    assert hits >= 1


def test_extract_cached_tokens_reads_anthropic_field() -> None:
    usage = MagicMock()
    usage.cache_read_input_tokens = 2048
    usage.prompt_tokens_details = None
    assert LLMRouter._extract_cached_tokens(usage) == 2048
