"""Memory quarantine workflow — freeze, review, restore, or delete (Gap #132)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Literal

import structlog
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import EpisodicMemoryRow, SemanticMemoryRow
from backend.db.session import session_scope
from backend.memory.audit import memory_audit_trail
from backend.metrics import record_memory_quarantine

logger = structlog.get_logger()

MemoryLayer = Literal["semantic", "episodic"]
QuarantineAction = Literal["quarantine", "restore", "delete"]


class MemoryQuarantineResult(BaseModel):
    """Outcome of a quarantine workflow action."""

    model_config = ConfigDict(strict=True, frozen=True)

    memory_id: uuid.UUID
    memory_layer: MemoryLayer
    action: QuarantineAction
    user_id: str = Field(..., min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=200)


class MemoryQuarantineError(Exception):
    """Raised when a quarantine action cannot be completed."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


async def _set_user_context(session: AsyncSession, user_id: str) -> None:
    await session.execute(
        text("SELECT set_config('app.user_id', :user_id, true)"),
        {"user_id": user_id},
    )


async def _get_semantic_row(
    session: AsyncSession,
    *,
    user_id: str,
    memory_id: uuid.UUID,
) -> SemanticMemoryRow | None:
    stmt = select(SemanticMemoryRow).where(
        SemanticMemoryRow.id == memory_id,
        SemanticMemoryRow.user_id == user_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _get_episodic_row(
    session: AsyncSession,
    *,
    user_id: str,
    memory_id: uuid.UUID,
) -> EpisodicMemoryRow | None:
    stmt = select(EpisodicMemoryRow).where(
        EpisodicMemoryRow.id == memory_id,
        EpisodicMemoryRow.user_id == user_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _log_quarantine_audit(
    *,
    trace_id: str,
    user_id: str,
    memory_layer: MemoryLayer,
    action: QuarantineAction,
    memory_id: uuid.UUID,
    reason: str,
    actor: str,
) -> None:
    memory_audit_trail.log_mutation(
        trace_id=trace_id,
        user_id=user_id,
        memory_layer=memory_layer,
        action=action,
        memory_id=str(memory_id),
        reason=reason,
        actor=actor,
    )
    logger.warning(
        "memory_quarantine_action",
        trace_id=trace_id,
        user_id=user_id,
        memory_layer=memory_layer,
        action=action,
        memory_id=str(memory_id),
        reason=reason,
        actor=actor,
    )
    record_memory_quarantine(memory_layer=memory_layer, action=action)


async def quarantine_memory(
    *,
    user_id: str,
    memory_id: uuid.UUID,
    memory_layer: MemoryLayer,
    reason: str,
    trace_id: str,
    actor: str = "system",
) -> MemoryQuarantineResult:
    """Freeze a memory segment so it is excluded from retrieval."""
    cleaned_reason = reason.strip()
    if not cleaned_reason:
        msg = "Quarantine reason is required"
        raise MemoryQuarantineError(msg)

    now = datetime.now(UTC)
    async with session_scope() as session:
        await _set_user_context(session, user_id)
        if memory_layer == "semantic":
            semantic_row = await _get_semantic_row(session, user_id=user_id, memory_id=memory_id)
            if semantic_row is None:
                raise MemoryQuarantineError(f"Semantic memory not found: {memory_id}")
            if semantic_row.quarantined:
                raise MemoryQuarantineError(f"Semantic memory already quarantined: {memory_id}")
            await session.execute(
                update(SemanticMemoryRow)
                .where(
                    SemanticMemoryRow.id == memory_id,
                    SemanticMemoryRow.user_id == user_id,
                )
                .values(
                    quarantined=True,
                    quarantine_reason=cleaned_reason[:200],
                    quarantined_at=now,
                ),
            )
        else:
            episodic_row = await _get_episodic_row(session, user_id=user_id, memory_id=memory_id)
            if episodic_row is None:
                raise MemoryQuarantineError(f"Episodic memory not found: {memory_id}")
            if episodic_row.quarantined:
                raise MemoryQuarantineError(f"Episodic memory already quarantined: {memory_id}")
            await session.execute(
                update(EpisodicMemoryRow)
                .where(
                    EpisodicMemoryRow.id == memory_id,
                    EpisodicMemoryRow.user_id == user_id,
                )
                .values(
                    quarantined=True,
                    quarantine_reason=cleaned_reason[:200],
                    quarantined_at=now,
                ),
            )

    _log_quarantine_audit(
        trace_id=trace_id,
        user_id=user_id,
        memory_layer=memory_layer,
        action="quarantine",
        memory_id=memory_id,
        reason=cleaned_reason,
        actor=actor,
    )
    return MemoryQuarantineResult(
        memory_id=memory_id,
        memory_layer=memory_layer,
        action="quarantine",
        user_id=user_id,
        reason=cleaned_reason,
    )


async def restore_memory(
    *,
    user_id: str,
    memory_id: uuid.UUID,
    memory_layer: MemoryLayer,
    trace_id: str,
    actor: str = "admin",
    reason: str = "restored_after_review",
) -> MemoryQuarantineResult:
    """Restore a quarantined memory segment after review."""
    async with session_scope() as session:
        await _set_user_context(session, user_id)
        if memory_layer == "semantic":
            semantic_row = await _get_semantic_row(session, user_id=user_id, memory_id=memory_id)
            if semantic_row is None:
                raise MemoryQuarantineError(f"Semantic memory not found: {memory_id}")
            if not semantic_row.quarantined:
                raise MemoryQuarantineError(f"Semantic memory is not quarantined: {memory_id}")
            await session.execute(
                update(SemanticMemoryRow)
                .where(
                    SemanticMemoryRow.id == memory_id,
                    SemanticMemoryRow.user_id == user_id,
                )
                .values(
                    quarantined=False,
                    quarantine_reason=None,
                    quarantined_at=None,
                ),
            )
        else:
            episodic_row = await _get_episodic_row(session, user_id=user_id, memory_id=memory_id)
            if episodic_row is None:
                raise MemoryQuarantineError(f"Episodic memory not found: {memory_id}")
            if not episodic_row.quarantined:
                raise MemoryQuarantineError(f"Episodic memory is not quarantined: {memory_id}")
            await session.execute(
                update(EpisodicMemoryRow)
                .where(
                    EpisodicMemoryRow.id == memory_id,
                    EpisodicMemoryRow.user_id == user_id,
                )
                .values(
                    quarantined=False,
                    quarantine_reason=None,
                    quarantined_at=None,
                ),
            )

    _log_quarantine_audit(
        trace_id=trace_id,
        user_id=user_id,
        memory_layer=memory_layer,
        action="restore",
        memory_id=memory_id,
        reason=reason,
        actor=actor,
    )
    return MemoryQuarantineResult(
        memory_id=memory_id,
        memory_layer=memory_layer,
        action="restore",
        user_id=user_id,
        reason=reason,
    )


async def delete_memory(
    *,
    user_id: str,
    memory_id: uuid.UUID,
    memory_layer: MemoryLayer,
    trace_id: str,
    actor: str = "admin",
    reason: str = "confirmed_malicious",
) -> MemoryQuarantineResult:
    """Permanently delete a quarantined memory segment."""
    async with session_scope() as session:
        await _set_user_context(session, user_id)
        if memory_layer == "semantic":
            semantic_row = await _get_semantic_row(session, user_id=user_id, memory_id=memory_id)
            if semantic_row is None:
                raise MemoryQuarantineError(f"Semantic memory not found: {memory_id}")
            await session.execute(
                delete(SemanticMemoryRow).where(
                    SemanticMemoryRow.id == memory_id,
                    SemanticMemoryRow.user_id == user_id,
                ),
            )
        else:
            episodic_row = await _get_episodic_row(session, user_id=user_id, memory_id=memory_id)
            if episodic_row is None:
                raise MemoryQuarantineError(f"Episodic memory not found: {memory_id}")
            await session.execute(
                delete(EpisodicMemoryRow).where(
                    EpisodicMemoryRow.id == memory_id,
                    EpisodicMemoryRow.user_id == user_id,
                ),
            )

    _log_quarantine_audit(
        trace_id=trace_id,
        user_id=user_id,
        memory_layer=memory_layer,
        action="delete",
        memory_id=memory_id,
        reason=reason,
        actor=actor,
    )
    return MemoryQuarantineResult(
        memory_id=memory_id,
        memory_layer=memory_layer,
        action="delete",
        user_id=user_id,
        reason=reason,
    )
