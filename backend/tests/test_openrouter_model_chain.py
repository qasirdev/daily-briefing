"""Tests for OpenRouter model-chain settings and request wiring."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.llm.router import LLMRouter
from backend.settings import Settings


def test_openrouter_model_chain_from_env_list() -> None:
    settings = Settings(
        llm_openrouter_models="openai/gpt-oss-120b:free,openai/gpt-4o-mini,google/gemini-2.0-flash-001",
        llm_primary_model="ignored/when-list-set",
    )
    assert settings.openrouter_model_chain == [
        "openai/gpt-oss-120b:free",
        "openai/gpt-4o-mini",
        "google/gemini-2.0-flash-001",
    ]


def test_openrouter_model_chain_falls_back_to_primary() -> None:
    settings = Settings(
        llm_openrouter_models="",
        llm_primary_model="openai/gpt-4o-mini",
    )
    assert settings.openrouter_model_chain == ["openai/gpt-4o-mini"]


def test_openrouter_model_chain_dedupes_preserving_order() -> None:
    settings = Settings(
        llm_openrouter_models="openai/gpt-4o-mini,openai/gpt-oss-120b:free,openai/gpt-4o-mini",
    )
    assert settings.openrouter_model_chain == [
        "openai/gpt-4o-mini",
        "openai/gpt-oss-120b:free",
    ]


@pytest.mark.asyncio
async def test_openrouter_request_includes_fallback_extra_body() -> None:
    settings = Settings(
        openrouter_api_key="test-key",
        llm_openrouter_models="openai/gpt-oss-120b:free,openai/gpt-4o-mini",
        llm_openrouter_route="fallback",
    )
    router = LLMRouter(settings)

    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content="ok"))]
    completion.usage = MagicMock(total_tokens=10)
    completion.model = "openai/gpt-4o-mini"

    create_mock = AsyncMock(return_value=completion)
    with patch.object(router._primary.chat.completions, "create", create_mock):
        result = await router._call_provider(
            client=router._primary,
            model="openai/gpt-oss-120b:free",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=100,
            trace_id="e" * 32,
            agent_id="focus",
            openrouter_models=["openai/gpt-oss-120b:free", "openai/gpt-4o-mini"],
        )

    assert result.model_used == "openai/gpt-4o-mini"
    create_mock.assert_awaited_once()
    kwargs = create_mock.await_args.kwargs
    assert kwargs["model"] == "openai/gpt-oss-120b:free"
    assert kwargs["extra_body"] == {
        "models": ["openai/gpt-oss-120b:free", "openai/gpt-4o-mini"],
        "route": "fallback",
    }


@pytest.mark.asyncio
async def test_local_provider_does_not_send_openrouter_extra_body() -> None:
    settings = Settings(
        local_llm_enabled=True,
        llm_openrouter_models="openai/gpt-oss-120b:free,openai/gpt-4o-mini",
    )
    router = LLMRouter(settings)
    assert router._fallback is not None

    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content="ok"))]
    completion.usage = MagicMock(total_tokens=5)
    completion.model = "local/test"

    create_mock = AsyncMock(return_value=completion)
    with patch.object(router._fallback.chat.completions, "create", create_mock):
        await router._call_provider(
            client=router._fallback,
            model="local/test",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=50,
            trace_id="f" * 32,
            agent_id="focus",
            openrouter_models=None,
        )

    kwargs = create_mock.await_args.kwargs
    assert "extra_body" not in kwargs
