"""Memory consolidation — working→episodic distillation and semantic pruning."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import text

from backend.db.session import session_scope
from backend.memory.episodic import EpisodicMemoryStore
from backend.settings import Settings, get_settings

logger = structlog.get_logger()

_default_episodic = EpisodicMemoryStore()


def distill_working_snippets(snippets: list[str] | tuple[str, ...]) -> str:
    """Distill working memory snippets into a concise episodic lesson."""
    cleaned = [str(item).strip() for item in snippets if str(item).strip()]
    if not cleaned:
        return ""
    combined = " → ".join(cleaned[-5:])
    return combined[:2000]


async def distill_working_to_episodic(
    *,
    user_id: str,
    session_id: str,
    working_context: list[str] | tuple[str, ...],
    store: EpisodicMemoryStore | None = None,
) -> str | None:
    """Distill working memory context into an episodic lesson at session end."""
    summary = distill_working_snippets(working_context)
    if not summary:
        return None
    resolved_store = store or _default_episodic
    lesson_id = await resolved_store.store_lesson(
        user_id=user_id,
        session_id=session_id,
        lesson_type="session_summary",
        summary=summary,
        metadata={"snippet_count": len(working_context)},
    )
    logger.info(
        "working_memory_distilled",
        user_id=user_id,
        session_id=session_id,
        lesson_id=str(lesson_id),
    )
    return str(lesson_id)


async def consolidate_semantic_memory(
    *,
    user_id: str,
    max_age_days: int = 90,
    settings: Settings | None = None,
) -> int:
    """Prune semantic memory rows older than max_age_days."""
    resolved_settings = settings or get_settings()
    if not resolved_settings.enable_semantic_memory_retrieval:
        return 0

    cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
    async with session_scope() as session:
        await session.execute(
            text("SELECT set_config('app.user_id', :user_id, true)"),
            {"user_id": user_id},
        )
        result = await session.execute(
            text(
                """
                DELETE FROM semantic_memory
                WHERE user_id = :user_id AND created_at < :cutoff
                """,
            ),
            {"user_id": user_id, "cutoff": cutoff},
        )
    deleted = int(getattr(result, "rowcount", 0) or 0)
    logger.info(
        "semantic_memory_consolidated",
        user_id=user_id,
        max_age_days=max_age_days,
        deleted_count=deleted,
    )
    return deleted
