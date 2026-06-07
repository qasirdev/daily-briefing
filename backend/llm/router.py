"""LLM routing with OpenRouter primary and local fallback."""

from __future__ import annotations

import time
from typing import Any, Literal

import httpx
import structlog
from openai import APIConnectionError, APIError, APIStatusError, AsyncOpenAI
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from backend.llm.models import LLMResponse
from backend.llm.prompt_cache import infer_cache_provider
from backend.llm.usage import (
    extract_completion_tokens,
    extract_cost_usd,
    extract_prompt_tokens,
)
from backend.metrics import record_llm_cache_usage, record_llm_fallback, record_llm_tokens
from backend.security.pii import mask_pii
from backend.settings import Settings
from backend.telemetry import start_async_span

logger = structlog.get_logger()

DEFAULT_INPUT_BUDGET = 8_000
DEFAULT_OUTPUT_BUDGET = 2_000
OPENROUTER_MAX_CHAIN_MODELS = 3

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
        self._openrouter_models = settings.openrouter_model_chain
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
    def primary_model(self) -> str:
        return self._primary_openrouter_model

    @property
    def fallback_model(self) -> str:
        return self._settings.local_llm_model_id or self._settings.llm_fallback_model

    @property
    def _primary_openrouter_model(self) -> str:
        if self._openrouter_models:
            return self._openrouter_models[0]
        return self._settings.llm_primary_model

    async def generate(
        self,
        *,
        messages: list[dict[str, Any]],
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

        use_local = force_local or (
            data_classification == "confidential_pii" and self._fallback is not None
        )
        if use_local:
            try:
                return await self._generate_local(
                    messages=messages,
                    max_tokens=output_budget,
                    trace_id=trace_id,
                    agent_id=agent_id,
                    reason="pii" if data_classification == "confidential_pii" else "forced",
                )
            except LLMError as local_error:
                if not self._settings.openrouter_api_key:
                    raise
                logger.warning(
                    "llm_local_failed_using_masked_primary",
                    trace_id=trace_id,
                    error=str(local_error),
                    reason="pii" if data_classification == "confidential_pii" else "forced",
                )
                outbound_messages = self._prepare_outbound_messages(
                    messages,
                    data_classification=data_classification,
                )
                return await self._call_primary_with_retry(
                    messages=outbound_messages,
                    max_tokens=output_budget,
                    trace_id=trace_id,
                    agent_id=agent_id,
                )

        outbound_messages = self._prepare_outbound_messages(
            messages,
            data_classification=data_classification,
        )

        try:
            return await self._call_primary_with_retry(
                messages=outbound_messages,
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

    @staticmethod
    def _mask_message_content(content: str) -> str:
        return mask_pii(content)

    @classmethod
    def _prepare_outbound_messages(
        cls,
        messages: list[dict[str, Any]],
        *,
        data_classification: DataClassification,
    ) -> list[dict[str, Any]]:
        if data_classification not in {"confidential", "confidential_pii"}:
            return messages
        outbound: list[dict[str, Any]] = []
        for message in messages:
            content = message.get("content", "")
            if isinstance(content, str):
                outbound.append(
                    {"role": message["role"], "content": cls._mask_message_content(content)},
                )
                continue
            if isinstance(content, list):
                masked_blocks: list[Any] = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        masked_text = cls._mask_message_content(str(text))
                        masked_blocks.append({**block, "text": masked_text})
                    else:
                        masked_blocks.append(block)
                outbound.append({"role": message["role"], "content": masked_blocks})
                continue
            outbound.append(message)
        return outbound

    async def _fallback_from_primary_error(
        self,
        *,
        primary_error: BaseException,
        messages: list[dict[str, Any]],
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
            from_model=self._primary_openrouter_model,
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
        messages: list[dict[str, Any]],
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
        messages: list[dict[str, Any]],
        max_tokens: int,
        trace_id: str,
        agent_id: str,
    ) -> LLMResponse:
        models = list(self._openrouter_models) or [self._primary_openrouter_model]
        errors: list[str] = []
        chain_models = models[:OPENROUTER_MAX_CHAIN_MODELS]
        overflow_models = models[OPENROUTER_MAX_CHAIN_MODELS:]

        if len(chain_models) > 1:
            try:
                return await self._call_provider(
                    client=self._primary,
                    model=chain_models[0],
                    messages=messages,
                    max_tokens=max_tokens,
                    trace_id=trace_id,
                    agent_id=agent_id,
                    openrouter_models=chain_models,
                )
            except LLMError as exc:
                errors.append(f"chain: {exc}")
                logger.warning(
                    "openrouter_model_chain_failed",
                    trace_id=trace_id,
                    error=str(exc),
                    models=chain_models,
                    overflow_models=overflow_models or None,
                )

        if len(chain_models) > 1 and errors:
            fallback_models = chain_models[1:] + overflow_models
        else:
            fallback_models = chain_models + overflow_models
        for candidate in fallback_models:
            try:
                return await self._call_provider(
                    client=self._primary,
                    model=candidate,
                    messages=messages,
                    max_tokens=max_tokens,
                    trace_id=trace_id,
                    agent_id=agent_id,
                    openrouter_models=None,
                )
            except LLMError as exc:
                errors.append(f"{candidate}: {exc}")
                continue

        msg = "; ".join(errors) if errors else "All LLM providers returned empty responses"
        raise LLMError(msg)

    async def _call_provider(
        self,
        *,
        client: AsyncOpenAI,
        model: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        trace_id: str,
        agent_id: str,
        openrouter_models: list[str] | None = None,
    ) -> LLMResponse:
        async with start_async_span(f"llm.{model}.generate", llm_model=model):
            start = time.perf_counter()
            try:
                if openrouter_models:
                    completion = await client.chat.completions.create(
                        model=model,
                        messages=messages,  # type: ignore[arg-type]
                        max_tokens=max_tokens,
                        extra_body={
                            "models": openrouter_models,
                            "route": self._settings.llm_openrouter_route,
                        },
                    )
                else:
                    completion = await client.chat.completions.create(
                        model=model,
                        messages=messages,  # type: ignore[arg-type]
                        max_tokens=max_tokens,
                    )
            except httpx.TimeoutException as exc:
                raise LLMError("LLM request timed out") from exc
            except APIConnectionError as exc:
                raise LLMError("LLM connection error") from exc
            except APIStatusError as exc:
                raise LLMError(str(exc)) from exc
            except APIError as exc:
                raise LLMError(str(exc)) from exc

            latency_ms = int((time.perf_counter() - start) * 1000)
            choice = completion.choices[0].message.content or ""
            if not choice.strip():
                model_used = completion.model or model
                msg = f"Empty response from model {model_used}"
                raise LLMError(msg)
            usage = completion.usage
            model_used = completion.model or model
            tokens_used = usage.total_tokens if usage else len(choice) // 4
            prompt_tokens = extract_prompt_tokens(usage) or 0
            completion_tokens = extract_completion_tokens(usage) or 0
            cost_usd = extract_cost_usd(usage) or 0.0
            record_llm_tokens(agent_id=agent_id, model=model_used, tokens=tokens_used)
            cached_tokens = self._extract_cached_tokens(usage)
            if self._settings.enable_prompt_caching:
                record_llm_cache_usage(
                    provider=infer_cache_provider(model_used),
                    model=model_used,
                    cached_tokens=cached_tokens,
                )

            logger.info(
                "llm_generation_complete",
                trace_id=trace_id,
                model=model_used,
                model_requested=model,
                openrouter_models=openrouter_models,
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd,
                cached_tokens=cached_tokens,
                latency_ms=latency_ms,
            )

            return LLMResponse(
                content=choice,
                model_used=model_used,
                tokens_used=tokens_used,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
            )

    @staticmethod
    def _extract_cached_tokens(usage: object | None) -> int:
        """Extract cached prompt tokens from provider usage metadata."""
        if usage is None:
            return 0
        cache_read = getattr(usage, "cache_read_input_tokens", None)
        if isinstance(cache_read, int) and cache_read > 0:
            return cache_read
        details = getattr(usage, "prompt_tokens_details", None)
        if details is not None:
            cached = getattr(details, "cached_tokens", None)
            if isinstance(cached, int) and cached > 0:
                return cached
        return 0
