"""Semantic memory store backed by pgvector on PostgreSQL/Supabase."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

import structlog
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import SemanticMemoryRow
from backend.db.session import session_scope
from backend.memory.ingestion import (
    SemanticIngestionRejected,
    SourceTrust,
    validate_semantic_content,
)
from backend.metrics import record_security_violation
from backend.settings import Settings, get_settings

logger = structlog.get_logger()

SourceType = Literal["briefing", "preference", "task", "calendar", "lesson"]


class SemanticMemoryRecord(BaseModel):
    """Retrieved semantic memory row with similarity score."""

    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    user_id: str = Field(..., min_length=1, max_length=64)
    content: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1, max_length=32)
    source_id: str | None = Field(default=None, max_length=64)
    source_trust: str = Field(default="internal", min_length=1, max_length=16)
    content_hash: str = Field(default="", max_length=64)
    similarity: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime


class SemanticMemoryStore:
    """Persist and retrieve semantic memory vectors with user isolation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    @property
    def embedding_dim(self) -> int:
        return self._settings.semantic_memory_embedding_dim

    async def _set_user_context(self, session: AsyncSession, user_id: str) -> None:
        await session.execute(
            text("SELECT set_config('app.user_id', :user_id, true)"),
            {"user_id": user_id},
        )

    async def store(
        self,
        *,
        user_id: str,
        content: str,
        embedding: list[float],
        source_type: SourceType,
        source_id: str | None = None,
        source_trust: SourceTrust = "internal",
        trace_id: str = "",
        agent_id: str = "focus",
    ) -> uuid.UUID:
        """Persist a semantic memory embedding for a user."""
        if len(embedding) != self.embedding_dim:
            msg = (
                f"Embedding dimension mismatch: expected {self.embedding_dim}, got {len(embedding)}"
            )
            raise ValueError(msg)

        validation = validate_semantic_content(
            content,
            trace_id=trace_id,
            source=f"semantic_store:{source_type}",
        )
        if not validation.accepted:
            record_security_violation(
                violation_type=validation.reason or "rag_poisoning",
                agent_id=agent_id,
            )
            raise SemanticIngestionRejected(
                reason=validation.reason or "rag_poisoning",
                matched_pattern=validation.matched_pattern,
            )

        memory_id = uuid.uuid4()
        row = SemanticMemoryRow(
            id=memory_id,
            user_id=user_id,
            content=content.strip(),
            embedding=embedding,
            source_type=source_type,
            source_id=source_id,
            source_trust=source_trust,
            content_hash=validation.content_hash,
            quarantined=False,
            created_at=datetime.now(UTC),
        )
        async with session_scope() as session:
            await self._set_user_context(session, user_id)
            session.add(row)
        logger.info(
            "semantic_memory_stored",
            user_id=user_id,
            memory_id=str(memory_id),
            source_type=source_type,
            source_trust=source_trust,
            content_hash=validation.content_hash,
        )
        return memory_id

    async def search_similar(
        self,
        *,
        user_id: str,
        embedding: list[float],
        top_k: int | None = None,
        min_similarity: float = 0.0,
    ) -> list[SemanticMemoryRecord]:
        """Search semantic memory by cosine similarity for a single user."""
        if len(embedding) != self.embedding_dim:
            msg = (
                f"Embedding dimension mismatch: expected {self.embedding_dim}, got {len(embedding)}"
            )
            raise ValueError(msg)

        limit = top_k or self._settings.semantic_memory_search_top_k
        embedding_literal = "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"

        query = text(
            """
            SELECT
                id,
                user_id,
                content,
                source_type,
                source_id,
                source_trust,
                content_hash,
                created_at,
                1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM semantic_memory
            WHERE user_id = :user_id
              AND quarantined = false
              AND (1 - (embedding <=> CAST(:embedding AS vector))) >= :min_similarity
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
            """,
        )

        async with session_scope() as session:
            await self._set_user_context(session, user_id)
            result = await session.execute(
                query,
                {
                    "embedding": embedding_literal,
                    "user_id": user_id,
                    "min_similarity": min_similarity,
                    "limit": limit,
                },
            )
            rows = result.mappings().all()

        return [
            SemanticMemoryRecord(
                id=row["id"],
                user_id=row["user_id"],
                content=row["content"],
                source_type=row["source_type"],
                source_id=row["source_id"],
                source_trust=row["source_trust"],
                content_hash=row["content_hash"],
                similarity=float(row["similarity"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def get_by_user(self, user_id: str, *, limit: int = 20) -> list[SemanticMemoryRecord]:
        """Return recent semantic memory rows for a user."""
        async with session_scope() as session:
            await self._set_user_context(session, user_id)
            stmt = (
                select(SemanticMemoryRow)
                .where(
                    SemanticMemoryRow.user_id == user_id,
                    SemanticMemoryRow.quarantined.is_(False),
                )
                .order_by(SemanticMemoryRow.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

        return [
            SemanticMemoryRecord(
                id=row.id,
                user_id=row.user_id,
                content=row.content,
                source_type=row.source_type,
                source_id=row.source_id,
                source_trust=row.source_trust,
                content_hash=row.content_hash,
                similarity=1.0,
                created_at=row.created_at,
            )
            for row in rows
        ]
