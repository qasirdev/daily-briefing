"""Fetch cumulative usage from the OpenRouter account API."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from backend.schemas.account_usage import AccountUsageResponse

logger = structlog.get_logger()


class OpenRouterAccountError(Exception):
    """OpenRouter account usage request failed."""


def _as_float(value: object | None) -> float | None:
    if isinstance(value, (int, float)) and value >= 0:
        return float(value)
    return None


def _parse_key_usage(payload: dict[str, Any]) -> AccountUsageResponse:
    data = payload.get("data")
    if not isinstance(data, dict):
        msg = "OpenRouter key response missing data"
        raise OpenRouterAccountError(msg)

    label = data.get("label")
    return AccountUsageResponse(
        available=True,
        source="openrouter_key",
        label=str(label) if isinstance(label, str) and label else None,
        usage_all_time_usd=_as_float(data.get("usage")),
        usage_daily_usd=_as_float(data.get("usage_daily")),
        usage_weekly_usd=_as_float(data.get("usage_weekly")),
        usage_monthly_usd=_as_float(data.get("usage_monthly")),
        limit_remaining_usd=_as_float(data.get("limit_remaining")),
        is_free_tier=bool(data.get("is_free_tier")) if "is_free_tier" in data else None,
    )


async def fetch_openrouter_key_usage(
    *,
    api_key: str,
    base_url: str,
) -> AccountUsageResponse:
    """Return cumulative spend for the configured OpenRouter API key."""
    url = f"{base_url.rstrip('/')}/key"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as exc:
        msg = f"OpenRouter key API returned {exc.response.status_code}"
        raise OpenRouterAccountError(msg) from exc
    except httpx.HTTPError as exc:
        msg = "OpenRouter key API request failed"
        raise OpenRouterAccountError(msg) from exc

    if not isinstance(payload, dict):
        msg = "OpenRouter key API returned invalid JSON"
        raise OpenRouterAccountError(msg)

    usage = _parse_key_usage(payload)
    logger.info(
        "openrouter_account_usage_fetched",
        label=usage.label,
        usage_all_time_usd=usage.usage_all_time_usd,
        usage_monthly_usd=usage.usage_monthly_usd,
    )
    return usage


def unavailable_account_usage(*, message: str) -> AccountUsageResponse:
    """Return a graceful unavailable payload for the usage endpoint."""
    return AccountUsageResponse(available=False, message=message)
