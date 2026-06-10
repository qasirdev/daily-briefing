"""Account usage endpoints."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Request

from backend.llm.openrouter_account import (
    OpenRouterAccountError,
    fetch_openrouter_key_usage,
    unavailable_account_usage,
)
from backend.schemas.account_usage import AccountUsageResponse
from backend.security.rate_limit import limiter
from backend.settings import Settings

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/usage", tags=["usage"])


@router.get("/account", response_model=AccountUsageResponse)
@limiter.limit("30/minute")
async def get_account_usage(request: Request) -> AccountUsageResponse:
    """Return cumulative OpenRouter spend for the configured API key."""
    settings: Settings = request.app.state.settings
    if not settings.openrouter_api_key:
        return unavailable_account_usage(message="OpenRouter API key is not configured")

    try:
        return await fetch_openrouter_key_usage(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
    except OpenRouterAccountError as exc:
        logger.warning("openrouter_account_usage_unavailable", error=str(exc))
        return unavailable_account_usage(message=str(exc))
