"""Reasoning feedback API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from backend.feedback.reasoning import store_reasoning_feedback
from backend.schemas.reasoning_feedback import (
    ReasoningFeedbackRequest,
    ReasoningFeedbackResponse,
)

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


@router.post(
    "/reasoning",
    response_model=ReasoningFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_reasoning_feedback(
    body: ReasoningFeedbackRequest,
) -> ReasoningFeedbackResponse:
    """Store human feedback on agent reasoning steps."""
    lesson_id = await store_reasoning_feedback(body)
    return ReasoningFeedbackResponse(
        stored=True,
        lesson_id=lesson_id,
        message="Reasoning feedback saved to episodic memory",
    )
