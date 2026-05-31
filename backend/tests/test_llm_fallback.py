"""Tests for LLM fallback behavior."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from openai import APIStatusError

from backend.llm.models import LLMResponse
from backend.llm.router import LLMError, LLMRouter
from backend.settings import Settings


@pytest.mark.asyncio
async def test_pii_forces_local_llm() -> None:
    settings = Settings(local_llm_enabled=True, local_llm_model_id="local/test")
    router = LLMRouter(settings)
    local_mock = AsyncMock(
        return_value=LLMResponse(
            content="{}",
            model_used="local/test",
            tokens_used=1,
            latency_ms=1,
        ),
    )
    with patch.object(router, "_generate_local", local_mock):
        result = await router.generate(
            messages=[{"role": "user", "content": "plan"}],
            trace_id="a" * 32,
            data_classification="confidential_pii",
            agent_id="focus",
        )
    assert result.model_used == "local/test"
    local_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_local_disabled_uses_masked_primary_for_pii() -> None:
    settings = Settings(local_llm_enabled=False, openrouter_api_key="test")
    router = LLMRouter(settings)
    primary_mock = AsyncMock(
        return_value=LLMResponse(
            content="{}",
            model_used="openai/gpt-4o-mini",
            tokens_used=10,
            latency_ms=5,
        ),
    )
    with patch.object(router, "_call_primary_with_retry", primary_mock):
        result = await router.generate(
            messages=[{"role": "user", "content": "email: user@example.com"}],
            trace_id="b" * 32,
            data_classification="confidential_pii",
            agent_id="focus",
        )
    assert result.model_used == "openai/gpt-4o-mini"
    primary_mock.assert_awaited_once()
    outbound = primary_mock.await_args.kwargs["messages"]
    assert "[REDACTED_EMAIL]" in outbound[0]["content"] or "user@example.com" not in outbound[0]["content"]


@pytest.mark.asyncio
async def test_pii_local_failure_falls_back_to_masked_primary() -> None:
    settings = Settings(
        local_llm_enabled=True,
        openrouter_api_key="test",
        llm_primary_model="openai/gpt-4o-mini",
    )
    router = LLMRouter(settings)
    primary_mock = AsyncMock(
        return_value=LLMResponse(
            content="{}",
            model_used="openai/gpt-4o-mini",
            tokens_used=12,
            latency_ms=4,
        ),
    )
    with (
        patch.object(
            router,
            "_generate_local",
            AsyncMock(side_effect=LLMError("Local LLM unavailable")),
        ),
        patch.object(router, "_call_primary_with_retry", primary_mock),
    ):
        result = await router.generate(
            messages=[{"role": "user", "content": "email: user@example.com"}],
            trace_id="d" * 32,
            data_classification="confidential_pii",
            agent_id="focus",
        )
    assert result.model_used == "openai/gpt-4o-mini"
    primary_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_rate_limit_triggers_fallback_when_enabled() -> None:
    settings = Settings(local_llm_enabled=True, openrouter_api_key="test")
    router = LLMRouter(settings)
    rate_error = APIStatusError(
        "rate limited",
        response=httpx.Response(429, request=httpx.Request("POST", "http://test")),
        body=None,
    )
    with (
        patch.object(router, "_call_primary_with_retry", AsyncMock(side_effect=rate_error)),
        patch.object(
            router,
            "_generate_local",
            AsyncMock(
                return_value=LLMResponse(
                    content="ok",
                    model_used="local/test",
                    tokens_used=2,
                    latency_ms=3,
                ),
            ),
        ) as local_mock,
    ):
        result = await router.generate(
            messages=[{"role": "user", "content": "hello"}],
            trace_id="c" * 32,
            agent_id="focus",
        )
    assert result.content == "ok"
    local_mock.assert_awaited_once()
