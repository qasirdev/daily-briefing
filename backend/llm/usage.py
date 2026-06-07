"""Extract token and cost details from provider usage objects."""

from __future__ import annotations


def _usage_mapping(usage: object) -> dict[str, object]:
    if hasattr(usage, "model_dump"):
        dumped = usage.model_dump()
        if isinstance(dumped, dict):
            return dumped
    if isinstance(usage, dict):
        return usage
    return {}


def extract_prompt_tokens(usage: object | None) -> int | None:
    """Return prompt/input token count when the provider reports it."""
    if usage is None:
        return None
    prompt_tokens = getattr(usage, "prompt_tokens", None)
    if isinstance(prompt_tokens, int) and prompt_tokens >= 0:
        return prompt_tokens
    mapped = _usage_mapping(usage).get("prompt_tokens")
    if isinstance(mapped, int) and mapped >= 0:
        return mapped
    return None


def extract_completion_tokens(usage: object | None) -> int | None:
    """Return completion/output token count when the provider reports it."""
    if usage is None:
        return None
    completion_tokens = getattr(usage, "completion_tokens", None)
    if isinstance(completion_tokens, int) and completion_tokens >= 0:
        return completion_tokens
    mapped = _usage_mapping(usage).get("completion_tokens")
    if isinstance(mapped, int) and mapped >= 0:
        return mapped
    return None


def extract_cost_usd(usage: object | None) -> float | None:
    """Return billed cost in USD when OpenRouter (or provider) reports it."""
    if usage is None:
        return None
    cost = getattr(usage, "cost", None)
    if isinstance(cost, (int, float)) and cost >= 0:
        return float(cost)
    mapped = _usage_mapping(usage).get("cost")
    if isinstance(mapped, (int, float)) and mapped >= 0:
        return float(mapped)
    return None
