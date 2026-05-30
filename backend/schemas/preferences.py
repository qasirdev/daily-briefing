"""User preference schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class UserPreference(BaseModel):
    """Learned user preference from briefing edits."""

    model_config = ConfigDict(strict=True)

    id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., min_length=1)
    preference_text: str = Field(..., min_length=1)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source_briefing_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PreferenceFeedbackRequest(BaseModel):
    """Feedback payload when a user edits a briefing."""

    model_config = ConfigDict(strict=True)

    user_id: str = Field(..., min_length=1)
    briefing_id: str = Field(..., min_length=1)
    original_content: str = ""
    edited_content: str = Field(..., min_length=1)


class PreferenceFeedbackResponse(BaseModel):
    """Response after processing preference feedback."""

    model_config = ConfigDict(strict=True)

    extracted: bool
    preference: UserPreference | None = None
    message: str = ""
