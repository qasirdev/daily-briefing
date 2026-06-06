"""Reasoning-level feedback schemas (Gap #69)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

FeedbackRating = Literal["correct", "incorrect", "partial"]


class ReasoningFeedbackRequest(BaseModel):
    """Human feedback on a specific agent reasoning step."""

    model_config = ConfigDict(strict=True)

    user_id: str = Field(..., min_length=1)
    briefing_id: str = Field(..., min_length=1)
    trace_id: str = Field(..., min_length=32, max_length=64)
    agent_id: str = Field(..., min_length=1, max_length=32)
    rating: FeedbackRating
    comment: str = Field(default="", max_length=2000)
    hitl_layer: str = Field(default="feedback", max_length=32)


class ReasoningFeedbackResponse(BaseModel):
    """Response after storing reasoning feedback."""

    model_config = ConfigDict(strict=True)

    stored: bool
    lesson_id: str = ""
    message: str = ""
