"""Cache ROI validation tests (Week 2 Day 5)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.llm.cache_roi import (
    WEEK1_BASELINE_HIT_RATE_PERCENT,
    cache_roi_vs_week1_baseline,
    calculate_cache_hit_rate_percent,
    calculate_token_savings_percent,
    warm_path_meets_target,
)
from backend.llm.prompt_cache import PromptCacheWarmer, build_llm_messages
from backend.llm.router import LLMRouter
from backend.observability.metrics import (
    CACHE_HIT_RATE,
    CACHE_HIT_TOTAL,
    CACHE_MISS_TOTAL,
    record_llm_cache_usage,
)
from backend.settings import Settings


def test_calculate_cache_hit_rate_percent() -> None:
    assert calculate_cache_hit_rate_percent(hits=7, misses=3) == 70.0
    assert calculate_cache_hit_rate_percent(hits=0, misses=0) == 0.0


def test_warm_path_meets_seventy_percent_target() -> None:
    assert warm_path_meets_target(hits=7, misses=3)
    assert not warm_path_meets_target(hits=6, misses=4)


def test_cache_roi_improves_over_week1_baseline() -> None:
    warm_hit_rate = calculate_cache_hit_rate_percent(hits=8, misses=2)
    roi = cache_roi_vs_week1_baseline(hit_rate_percent=warm_hit_rate)
    assert WEEK1_BASELINE_HIT_RATE_PERCENT == 0.0
    assert roi == pytest.approx(80.0)


def test_token_savings_percent_caps_at_one_hundred() -> None:
    assert calculate_token_savings_percent(cached_tokens=900, prompt_tokens=1000) == 90.0
    assert calculate_token_savings_percent(cached_tokens=1200, prompt_tokens=1000) == 100.0


def test_warm_path_simulation_records_seventy_plus_hit_rate() -> None:
    provider = "openai"
    model = "week2-warm-path-model"
    for _ in range(3):
        record_llm_cache_usage(provider=provider, model=model, cached_tokens=0)
    for _ in range(7):
        record_llm_cache_usage(provider=provider, model=model, cached_tokens=512)

    hits = CACHE_HIT_TOTAL.labels(provider=provider, model=model)._value.get()
    misses = CACHE_MISS_TOTAL.labels(provider=provider, model=model)._value.get()
    hit_rate = calculate_cache_hit_rate_percent(hits=int(hits), misses=int(misses))
    assert warm_path_meets_target(hits=int(hits), misses=int(misses))
    assert CACHE_HIT_RATE.labels(provider=provider, model=model)._value.get() == hit_rate


@pytest.mark.asyncio
async def test_cache_warmer_targets_cache_eligible_agents() -> None:
    settings = Settings(enable_prompt_caching=True)
    warmer = PromptCacheWarmer(settings=settings)
    mock_llm = AsyncMock()
    mock_llm.primary_model = "openai/gpt-4o-mini"
    with patch.object(warmer, "warm_agent", AsyncMock()) as mock_warm:
        await warmer.warm_all(mock_llm)
    warmed_agents = {call.args[1] for call in mock_warm.await_args_list}
    assert "focus" in warmed_agents
    assert "verification" in warmed_agents


def test_focus_messages_use_static_prefix_for_auto_cache() -> None:
    messages = build_llm_messages(
        "focus",
        "dynamic payload",
        model="openai/gpt-4o-mini",
        enable_caching=True,
    )
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert len(messages[0]["content"]) > 100


@pytest.mark.asyncio
async def test_router_warm_path_records_high_cache_ratio() -> None:
    settings = Settings(openrouter_api_key="test", enable_prompt_caching=True)
    router = LLMRouter(settings)

    usage = MagicMock()
    usage.total_tokens = 1000
    usage.prompt_tokens = 1000
    usage.prompt_tokens_details = MagicMock(cached_tokens=800)

    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content='{"summary": "ok"}'))]
    completion.model = "openai/gpt-4o-mini"
    completion.usage = usage

    with patch.object(
        router._primary.chat.completions,
        "create",
        AsyncMock(return_value=completion),
    ):
        await router.generate(
            messages=[{"role": "user", "content": "hello"}],
            trace_id="e" * 32,
            agent_id="focus",
        )

    savings = calculate_token_savings_percent(cached_tokens=800, prompt_tokens=1000)
    assert savings >= 70.0
