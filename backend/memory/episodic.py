"""Episodic memory store — distilled session lessons (CoALA layer 4)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

import structlog
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import EpisodicMemoryRow
from backend.db.session import session_scope
from backend.settings import Settings, get_settings

logger = structlog.get_logger()

LessonType = Literal[
    "session_summary",
    "disagreement",
    "optimization",
    "preference",
    "error_recovery",
]


class EpisodicLessonRecord(BaseModel):
    """Distilled episodic lesson — not raw conversation logs."""

    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    user_id: str = Field(..., min_length=1, max_length=64)
    session_id: str = Field(..., min_length=1, max_length=64)
    lesson_type: str = Field(..., min_length=1, max_length=32)
    summary: str = Field(..., min_length=1)
    version: int = Field(..., ge=1)
    superseded_by: uuid.UUID | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime


def _row_to_record(row: EpisodicMemoryRow) -> EpisodicLessonRecord:
    return EpisodicLessonRecord(
        id=row.id,
        user_id=row.user_id,
        session_id=row.session_id,
        lesson_type=row.lesson_type,
        summary=row.summary,
        version=row.version,
        superseded_by=row.superseded_by,
        metadata=dict(row.metadata_) if row.metadata_ else {},
        created_at=row.created_at,
    )


class EpisodicMemoryStore:
    """Persist and retrieve distilled episodic lessons with session isolation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def _set_user_context(self, session: AsyncSession, user_id: str) -> None:
        await session.execute(
            text("SELECT set_config('app.user_id', :user_id, true)"),
            {"user_id": user_id},
        )

    async def store_lesson(
        self,
        *,
        user_id: str,
        session_id: str,
        lesson_type: LessonType,
        summary: str,
        metadata: dict[str, object] | None = None,
    ) -> uuid.UUID:
        """Store a distilled lesson for a briefing session."""
        lesson_id = uuid.uuid4()
        row = EpisodicMemoryRow(
            id=lesson_id,
            user_id=user_id,
            session_id=session_id,
            lesson_type=lesson_type,
            summary=summary.strip(),
            version=1,
            superseded_by=None,
            metadata_=metadata or {},
            created_at=datetime.now(UTC),
        )
        async with session_scope() as session:
            await self._set_user_context(session, user_id)
            session.add(row)
        logger.info(
            "episodic_lesson_stored",
            user_id=user_id,
            session_id=session_id,
            lesson_type=lesson_type,
        )
        return lesson_id

    async def get_recent_lessons(
        self,
        *,
        user_id: str,
        limit: int | None = None,
        exclude_superseded: bool = True,
    ) -> list[EpisodicLessonRecord]:
        """Return recent episodic lessons for a user."""
        resolved_limit = limit or self._settings.episodic_memory_top_k
        async with session_scope() as session:
            await self._set_user_context(session, user_id)
            stmt = (
                select(EpisodicMemoryRow)
                .where(
                    EpisodicMemoryRow.user_id == user_id,
                    EpisodicMemoryRow.quarantined.is_(False),
                )
                .order_by(EpisodicMemoryRow.created_at.desc())
                .limit(resolved_limit * 2 if exclude_superseded else resolved_limit)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

        records = [_row_to_record(row) for row in rows]
        if exclude_superseded:
            records = [record for record in records if record.superseded_by is None]
        return records[:resolved_limit]

    async def get_session_lessons(
        self,
        *,
        user_id: str,
        session_id: str,
    ) -> list[EpisodicLessonRecord]:
        """Return lessons for a specific session."""
        async with session_scope() as session:
            await self._set_user_context(session, user_id)
            stmt = (
                select(EpisodicMemoryRow)
                .where(
                    EpisodicMemoryRow.user_id == user_id,
                    EpisodicMemoryRow.session_id == session_id,
                    EpisodicMemoryRow.superseded_by.is_(None),
                    EpisodicMemoryRow.quarantined.is_(False),
                )
                .order_by(EpisodicMemoryRow.created_at.asc())
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
        return [_row_to_record(row) for row in rows]

    async def supersede_lesson(
        self,
        *,
        user_id: str,
        old_lesson_id: uuid.UUID,
        session_id: str,
        lesson_type: LessonType,
        summary: str,
        metadata: dict[str, object] | None = None,
    ) -> uuid.UUID:
        """Create a new version and mark the old lesson as superseded."""
        async with session_scope() as session:
            await self._set_user_context(session, user_id)
            stmt = select(EpisodicMemoryRow).where(
                EpisodicMemoryRow.id == old_lesson_id,
                EpisodicMemoryRow.user_id == user_id,
            )
            result = await session.execute(stmt)
            old_row = result.scalar_one_or_none()
        if old_row is None:
            msg = f"Episodic lesson not found: {old_lesson_id}"
            raise ValueError(msg)

        new_version = old_row.version + 1
        new_id = uuid.uuid4()
        row = EpisodicMemoryRow(
            id=new_id,
            user_id=user_id,
            session_id=session_id,
            lesson_type=lesson_type,
            summary=summary.strip(),
            version=new_version,
            superseded_by=None,
            metadata_=metadata or {},
            created_at=datetime.now(UTC),
        )
        async with session_scope() as session:
            await self._set_user_context(session, user_id)
            session.add(row)
            await session.execute(
                update(EpisodicMemoryRow)
                .where(
                    EpisodicMemoryRow.id == old_lesson_id,
                    EpisodicMemoryRow.user_id == user_id,
                )
                .values(superseded_by=new_id),
            )
        return new_id
