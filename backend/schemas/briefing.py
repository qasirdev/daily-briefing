"""Briefing API schemas."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BriefingRequest(BaseModel):
    """Request body for briefing generation."""

    model_config = ConfigDict(strict=True)

    user_id: str = Field(..., min_length=1)
    target_date: date | None = None


class BriefingMetadata(BaseModel):
    """Execution metadata returned to clients."""

    model_config = ConfigDict(strict=True)

    trace_id: str = Field(..., min_length=32, max_length=64)
    total_tokens: int = Field(..., ge=0)
    execution_ms: int = Field(..., ge=0)
    agents_invoked: list[str] = Field(default_factory=list)


class BriefingResponse(BaseModel):
    """Briefing generation response."""

    model_config = ConfigDict(strict=True)

    status: Literal["success", "degraded", "failure", "awaiting_consent"]
    briefing: str = ""
    metadata: BriefingMetadata
    consent_context: str | None = None
