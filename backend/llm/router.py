"""LLM routing with OpenRouter primary and local fallback."""

from __future__ import annotations

import time
from typing import Literal

import httpx
import structlog
from openai import APIConnectionError, APIError, APIStatusError, AsyncOpenAI
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from backend.llm.models import LLMResponse
from backend.metrics import record_llm_fallback, record_llm_tokens
from backend.settings import Settings
from backend.telemetry import start_async_span

logger = structlog.get_logger()

DEFAULT_INPUT_BUDGET = 8_000
DEFAULT_OUTPUT_BUDGET = 2_000

DataClassification = Literal[
    "public",
    "internal",
    "confidential",
    "confidential_pii",
]


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

    @property
    def fallback_model(self) -> str:
        return self._settings.local_llm_model_id or self._settings.llm_fallback_model

    async def generate(
        self,
        *,
        messages: list[dict[str, str]],
        trace_id: str,
        input_budget: int = DEFAULT_INPUT_BUDGET,
        output_budget: int = DEFAULT_OUTPUT_BUDGET,
        force_local: bool = False,
        data_classification: DataClassification = "internal",
        agent_id: str = "llm_router",
    ) -> LLMResponse:
        estimated_input = sum(len(m.get("content", "")) for m in messages) // 4
        if estimated_input > input_budget * 2:
            msg = "Token budget exceeded for input"
            raise LLMError(msg)

        use_local = force_local or data_classification == "confidential_pii"
        if use_local:
            return await self._generate_local(
                messages=messages,
                max_tokens=output_budget,
                trace_id=trace_id,
                agent_id=agent_id,
                reason="pii" if data_classification == "confidential_pii" else "forced",
            )

        try:
            return await self._call_primary_with_retry(
                messages=messages,
                max_tokens=output_budget,
                trace_id=trace_id,
                agent_id=agent_id,
            )
        except httpx.TimeoutException as primary_error:
            if self._fallback is None:
                raise LLMError("LLM request timed out") from primary_error
            return await self._fallback_from_primary_error(
                primary_error=primary_error,
                messages=messages,
                max_tokens=output_budget,
                trace_id=trace_id,
                agent_id=agent_id,
                reason="timeout",
            )
        except (LLMError, APIStatusError, APIError, httpx.HTTPError) as primary_error:
            reason = "rate_limit" if _is_rate_limited(primary_error) else "provider_error"
            if self._fallback is None:
                raise LLMError(str(primary_error)) from primary_error
            return await self._fallback_from_primary_error(
                primary_error=primary_error,
                messages=messages,
                max_tokens=output_budget,
                trace_id=trace_id,
                agent_id=agent_id,
                reason=reason,
            )

    async def _fallback_from_primary_error(
        self,
        *,
        primary_error: BaseException,
        messages: list[dict[str, str]],
        max_tokens: int,
        trace_id: str,
        agent_id: str,
        reason: str,
    ) -> LLMResponse:
        logger.warning(
            "llm_primary_failed_using_fallback",
            trace_id=trace_id,
            error=str(primary_error),
            reason=reason,
        )
        record_llm_fallback(
            from_model=self._settings.llm_primary_model,
            to_model=self.fallback_model,
            reason=reason,
        )
        return await self._generate_local(
            messages=messages,
            max_tokens=max_tokens,
            trace_id=trace_id,
            agent_id=agent_id,
            reason=reason,
        )

    async def _generate_local(
        self,
        *,
        messages: list[dict[str, str]],
        max_tokens: int,
        trace_id: str,
        agent_id: str,
        reason: str,
    ) -> LLMResponse:
        if self._fallback is None:
            raise LLMError("Local LLM fallback is disabled")
        try:
            return await self._call_provider(
                client=self._fallback,
                model=self.fallback_model,
                messages=messages,
                max_tokens=max_tokens,
                trace_id=trace_id,
                agent_id=agent_id,
            )
        except LLMError as exc:
            msg = f"Local LLM unavailable after fallback ({reason}): {exc}"
            raise LLMError(msg) from exc

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
        agent_id: str,
    ) -> LLMResponse:
        return await self._call_provider(
            client=self._primary,
            model=self._settings.llm_primary_model,
            messages=messages,
            max_tokens=max_tokens,
            trace_id=trace_id,
            agent_id=agent_id,
        )

    async def _call_provider(
        self,
        *,
        client: AsyncOpenAI,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        trace_id: str,
        agent_id: str,
    ) -> LLMResponse:
        async with start_async_span(f"llm.{model}.generate", llm_model=model):
            start = time.perf_counter()
            try:
                completion = await client.chat.completions.create(
                    model=model,
                    messages=messages,  # type: ignore[arg-type]
                    max_tokens=max_tokens,
                )
            except httpx.TimeoutException as exc:
                raise LLMError("LLM request timed out") from exc
            except APIConnectionError as exc:
                raise LLMError("LLM connection error") from exc

            latency_ms = int((time.perf_counter() - start) * 1000)
            choice = completion.choices[0].message.content or ""
            usage = completion.usage
            tokens_used = usage.total_tokens if usage else len(choice) // 4
            record_llm_tokens(agent_id=agent_id, model=model, tokens=tokens_used)

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
