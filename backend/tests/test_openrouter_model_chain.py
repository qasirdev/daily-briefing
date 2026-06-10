"""Tests for OpenRouter model-chain settings and request wiring."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.llm.router import OPENROUTER_MAX_CHAIN_MODELS, LLMError, LLMRouter
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
    await_args = create_mock.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert kwargs["model"] == "openai/gpt-oss-120b:free"
    assert kwargs["extra_body"] == {
        "models": ["openai/gpt-oss-120b:free", "openai/gpt-4o-mini"],
        "route": "fallback",
    }


@pytest.mark.asyncio
async def test_openrouter_chain_caps_models_at_three() -> None:
    models = [
        "deepseek/deepseek-v4-flash",
        "google/gemini-2.5-flash-lite",
        "mistralai/mistral-small-3.1-24b-instruct",
        "meta-llama/llama-3.3-70b-instruct:free",
    ]
    settings = Settings(
        openrouter_api_key="test-key",
        llm_openrouter_models=",".join(models),
        llm_openrouter_route="fallback",
    )
    router = LLMRouter(settings)

    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content="ok"))]
    completion.usage = MagicMock(total_tokens=10)
    completion.model = models[0]

    create_mock = AsyncMock(return_value=completion)
    with patch.object(router._primary.chat.completions, "create", create_mock):
        await router._call_primary_with_retry(
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=100,
            trace_id="c" * 32,
            agent_id="focus",
        )

    await_args = create_mock.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert kwargs["extra_body"]["models"] == models[:OPENROUTER_MAX_CHAIN_MODELS]


@pytest.mark.asyncio
async def test_invalid_chain_model_falls_back_to_next_candidate() -> None:
    from openai import APIStatusError

    models = [
        "deepseek/deepseek-v4-flash",
        "google/gemini-2.5-flash-lite",
        "mistralai/mistral-small-3.1-24b",
    ]
    settings = Settings(
        openrouter_api_key="test-key",
        llm_openrouter_models=",".join(models),
        llm_openrouter_route="fallback",
    )
    router = LLMRouter(settings)

    chain_error = APIStatusError(
        "invalid model in chain",
        response=MagicMock(status_code=400),
        body={"error": {"message": "mistralai/mistral-small-3.1-24b is not a valid model ID"}},
    )
    good_completion = MagicMock()
    good_completion.choices = [MagicMock(message=MagicMock(content='{"summary":"ok"}'))]
    good_completion.usage = MagicMock(total_tokens=12)
    good_completion.model = models[1]

    create_mock = AsyncMock(side_effect=[chain_error, good_completion])
    with patch.object(router._primary.chat.completions, "create", create_mock):
        result = await router._call_primary_with_retry(
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=100,
            trace_id="d" * 32,
            agent_id="focus",
        )

    assert result.content == '{"summary":"ok"}'
    assert create_mock.await_count == 2
    second_call = create_mock.await_args_list[1].kwargs
    assert second_call["model"] == models[1]
    assert "extra_body" not in second_call


@pytest.mark.asyncio
async def test_empty_chain_response_falls_back_to_next_model() -> None:
    settings = Settings(
        openrouter_api_key="test-key",
        llm_openrouter_models="openai/gpt-oss-120b,openai/gpt-4o-mini",
        llm_openrouter_route="fallback",
    )
    router = LLMRouter(settings)

    empty_completion = MagicMock()
    empty_completion.choices = [MagicMock(message=MagicMock(content=""))]
    empty_completion.usage = MagicMock(total_tokens=0)
    empty_completion.model = "openai/gpt-oss-120b"

    good_completion = MagicMock()
    good_completion.choices = [MagicMock(message=MagicMock(content='{"summary":"ok"}'))]
    good_completion.usage = MagicMock(total_tokens=12)
    good_completion.model = "openai/gpt-4o-mini"

    create_mock = AsyncMock(side_effect=[empty_completion, good_completion])
    with patch.object(router._primary.chat.completions, "create", create_mock):
        result = await router._call_primary_with_retry(
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=100,
            trace_id="a" * 32,
            agent_id="focus",
        )

    assert result.content == '{"summary":"ok"}'
    assert result.model_used == "openai/gpt-4o-mini"
    assert create_mock.await_count == 2


@pytest.mark.asyncio
async def test_all_models_empty_raises_llm_error() -> None:
    settings = Settings(
        openrouter_api_key="test-key",
        llm_openrouter_models="openai/gpt-oss-120b,openai/gpt-4o-mini",
    )
    router = LLMRouter(settings)

    empty_completion = MagicMock()
    empty_completion.choices = [MagicMock(message=MagicMock(content=""))]
    empty_completion.usage = MagicMock(total_tokens=0)
    empty_completion.model = "openai/gpt-oss-120b"

    create_mock = AsyncMock(return_value=empty_completion)
    with patch.object(router._primary.chat.completions, "create", create_mock):
        with pytest.raises(LLMError, match="Empty response"):
            await router._call_primary_with_retry(
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=100,
                trace_id="b" * 32,
                agent_id="focus",
            )


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

    await_args = create_mock.await_args
    assert await_args is not None
    kwargs = await_args.kwargs
    assert "extra_body" not in kwargs
