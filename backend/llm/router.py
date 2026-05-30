"""LLM routing with OpenRouter primary and local fallback."""

from __future__ import annotations

import time

import httpx
import structlog
from openai import APIStatusError, AsyncOpenAI
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from backend.llm.models import LLMResponse
from backend.settings import Settings

logger = structlog.get_logger()

DEFAULT_INPUT_BUDGET = 8_000
DEFAULT_OUTPUT_BUDGET = 2_000


class LLMError(Exception):
    """Both LLM providers failed."""


def _is_rate_limited(exc: BaseException) -> bool:
    return isinstance(exc, APIStatusError) and exc.status_code == 429


class LLMRouter:
    """Route generation requests with fallback and token budgets."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._primary = AsyncOpenAI(
            api_key=settings.openrouter_api_key or "missing-key",
            base_url=settings.openrouter_base_url,
        )
        self._fallback: AsyncOpenAI | None = None
        if settings.local_llm_enabled:
            self._fallback = AsyncOpenAI(
                api_key="local",
                base_url=settings.local_llm_base_url,
            )

    async def generate(
        self,
        *,
        messages: list[dict[str, str]],
        trace_id: str,
        input_budget: int = DEFAULT_INPUT_BUDGET,
        output_budget: int = DEFAULT_OUTPUT_BUDGET,
        force_local: bool = False,
    ) -> LLMResponse:
        estimated_input = sum(len(m.get("content", "")) for m in messages) // 4
        if estimated_input > input_budget * 2:
            msg = "Token budget exceeded for input"
            raise LLMError(msg)

        if force_local:
            if self._fallback is None:
                raise LLMError("Local LLM fallback is disabled")
            return await self._call_provider(
                client=self._fallback,
                model=self._settings.llm_fallback_model,
                messages=messages,
                max_tokens=min(output_budget, DEFAULT_OUTPUT_BUDGET),
                trace_id=trace_id,
            )

        try:
            return await self._call_primary_with_retry(
                messages=messages,
                max_tokens=output_budget,
                trace_id=trace_id,
            )
        except (LLMError, APIStatusError, httpx.HTTPError) as primary_error:
            if self._fallback is None:
                raise LLMError(str(primary_error)) from primary_error
            logger.warning(
                "llm_primary_failed_using_fallback",
                trace_id=trace_id,
                error=str(primary_error),
            )
            return await self._call_provider(
                client=self._fallback,
                model=self._settings.llm_fallback_model,
                messages=messages,
                max_tokens=output_budget,
                trace_id=trace_id,
            )

    @retry(
        retry=retry_if_exception(_is_rate_limited),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(2),
        reraise=True,
    )
    async def _call_primary_with_retry(
        self,
        *,
        messages: list[dict[str, str]],
        max_tokens: int,
        trace_id: str,
    ) -> LLMResponse:
        return await self._call_provider(
            client=self._primary,
            model=self._settings.llm_primary_model,
            messages=messages,
            max_tokens=max_tokens,
            trace_id=trace_id,
        )

    async def _call_provider(
        self,
        *,
        client: AsyncOpenAI,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        trace_id: str,
    ) -> LLMResponse:
        start = time.perf_counter()
        try:
            completion = await client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
            )
        except httpx.TimeoutException as exc:
            raise LLMError("LLM request timed out") from exc

        latency_ms = int((time.perf_counter() - start) * 1000)
        choice = completion.choices[0].message.content or ""
        usage = completion.usage
        tokens_used = usage.total_tokens if usage else len(choice) // 4

        logger.info(
            "llm_generation_complete",
            trace_id=trace_id,
            model=model,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )

        return LLMResponse(
            content=choice,
            model_used=model,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
        )
