"""OpenRouter account usage response schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class AccountUsageResponse(BaseModel):
    """Sanitized OpenRouter usage for the configured API key."""

    available: bool
    source: Literal["openrouter_key", "unavailable"] = "unavailable"
    label: str | None = None
    usage_all_time_usd: float | None = Field(default=None, ge=0.0)
    usage_daily_usd: float | None = Field(default=None, ge=0.0)
    usage_weekly_usd: float | None = Field(default=None, ge=0.0)
    usage_monthly_usd: float | None = Field(default=None, ge=0.0)
    limit_remaining_usd: float | None = Field(default=None, ge=0.0)
    is_free_tier: bool | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    message: str | None = None
