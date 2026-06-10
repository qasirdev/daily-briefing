"""Reasoning-level feedback storage (Gap #69)."""

from __future__ import annotations

import structlog

from backend.memory.episodic import EpisodicMemoryStore
from backend.schemas.reasoning_feedback import ReasoningFeedbackRequest

logger = structlog.get_logger()

_default_store = EpisodicMemoryStore()


async def store_reasoning_feedback(
    body: ReasoningFeedbackRequest,
    *,
    store: EpisodicMemoryStore | None = None,
) -> str:
    """Persist reasoning feedback as an episodic lesson."""
    resolved_store = store or _default_store
    summary = (
        f"[{body.rating}] agent={body.agent_id} trace={body.trace_id[:8]}… "
        f"{body.comment.strip() or 'no comment'}"
    )
    lesson_id = await resolved_store.store_lesson(
        user_id=body.user_id,
        session_id=body.briefing_id,
        lesson_type="optimization",
        summary=summary[:2000],
        metadata={
            "feedback_type": "reasoning_feedback",
            "agent_id": body.agent_id,
            "trace_id": body.trace_id,
            "rating": body.rating,
            "hitl_layer": body.hitl_layer or "feedback",
        },
    )
    logger.info(
        "reasoning_feedback_stored",
        user_id=body.user_id,
        agent_id=body.agent_id,
        lesson_id=str(lesson_id),
        rating=body.rating,
    )
    return str(lesson_id)
