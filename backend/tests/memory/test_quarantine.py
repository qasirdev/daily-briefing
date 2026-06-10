"""Tests for memory quarantine workflow (Gap #132)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.db.models import EpisodicMemoryRow, SemanticMemoryRow
from backend.memory.audit import memory_audit_trail
from backend.memory.episodic import EpisodicMemoryStore
from backend.memory.quarantine import (
    MemoryQuarantineError,
    delete_memory,
    quarantine_memory,
    restore_memory,
)

TRACE_ID = "f" * 32


def _session_context(mock_session: AsyncMock) -> type:
    class _SessionContext:
        async def __aenter__(self) -> AsyncMock:
            return mock_session

        async def __aexit__(self, *args: object) -> None:
            return None

    return _SessionContext


@pytest.mark.asyncio
async def test_quarantine_semantic_memory_records_audit_and_metric() -> None:
    memory_audit_trail.clear()
    memory_id = uuid.uuid4()
    row = SemanticMemoryRow(
        id=memory_id,
        user_id="user-1",
        content="Poisoned summary",
        embedding=[0.1] * 1536,
        source_type="briefing",
        source_id=None,
        source_trust="internal",
        content_hash="abc",
        quarantined=False,
        created_at=datetime.now(UTC),
    )
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = row
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch(
        "backend.memory.quarantine.session_scope",
        return_value=_session_context(mock_session)(),
    ):
        with patch("backend.memory.quarantine.record_memory_quarantine") as mock_metric:
            result = await quarantine_memory(
                user_id="user-1",
                memory_id=memory_id,
                memory_layer="semantic",
                reason="suspected poisoning",
                trace_id=TRACE_ID,
                actor="admin",
            )

    assert result.action == "quarantine"
    assert result.memory_layer == "semantic"
    assert len(memory_audit_trail.mutations) == 1
    assert memory_audit_trail.mutations[0].action == "quarantine"
    mock_metric.assert_called_once_with(memory_layer="semantic", action="quarantine")
    mock_session.execute.assert_awaited()


@pytest.mark.asyncio
async def test_quarantine_rejects_missing_memory() -> None:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch(
        "backend.memory.quarantine.session_scope",
        return_value=_session_context(mock_session)(),
    ):
        with pytest.raises(MemoryQuarantineError, match="not found"):
            await quarantine_memory(
                user_id="user-1",
                memory_id=uuid.uuid4(),
                memory_layer="semantic",
                reason="suspected poisoning",
                trace_id=TRACE_ID,
            )


@pytest.mark.asyncio
async def test_restore_semantic_memory_clears_quarantine_flags() -> None:
    memory_audit_trail.clear()
    memory_id = uuid.uuid4()
    row = SemanticMemoryRow(
        id=memory_id,
        user_id="user-1",
        content="Reviewed summary",
        embedding=[0.1] * 1536,
        source_type="briefing",
        source_id=None,
        source_trust="internal",
        content_hash="abc",
        quarantined=True,
        quarantine_reason="suspected poisoning",
        quarantined_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
    )
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = row
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch(
        "backend.memory.quarantine.session_scope",
        return_value=_session_context(mock_session)(),
    ):
        result = await restore_memory(
            user_id="user-1",
            memory_id=memory_id,
            memory_layer="semantic",
            trace_id=TRACE_ID,
        )

    assert result.action == "restore"
    assert memory_audit_trail.mutations[-1].action == "restore"


@pytest.mark.asyncio
async def test_delete_episodic_memory_records_delete_action() -> None:
    memory_audit_trail.clear()
    memory_id = uuid.uuid4()
    row = EpisodicMemoryRow(
        id=memory_id,
        user_id="user-1",
        session_id="session-1",
        lesson_type="session_summary",
        summary="Confirmed malicious lesson",
        version=1,
        metadata_={},
        quarantined=True,
        created_at=datetime.now(UTC),
    )
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = row
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch(
        "backend.memory.quarantine.session_scope",
        return_value=_session_context(mock_session)(),
    ):
        with patch("backend.memory.quarantine.record_memory_quarantine") as mock_metric:
            result = await delete_memory(
                user_id="user-1",
                memory_id=memory_id,
                memory_layer="episodic",
                trace_id=TRACE_ID,
            )

    assert result.action == "delete"
    assert result.memory_layer == "episodic"
    mock_metric.assert_called_once_with(memory_layer="episodic", action="delete")


@pytest.mark.asyncio
async def test_episodic_store_excludes_quarantined_lessons() -> None:
    store = EpisodicMemoryStore()
    mock_session = AsyncMock()
    active = EpisodicMemoryRow(
        id=uuid.uuid4(),
        user_id="user-1",
        session_id="session-1",
        lesson_type="session_summary",
        summary="Safe lesson",
        version=1,
        metadata_={},
        quarantined=False,
        created_at=datetime.now(UTC),
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [active]
    mock_session.execute = AsyncMock(return_value=mock_result)

    with patch(
        "backend.memory.episodic.session_scope",
        return_value=_session_context(mock_session)(),
    ):
        records = await store.get_recent_lessons(user_id="user-1", limit=5)

    assert len(records) == 1
    stmt = mock_session.execute.await_args.args[0]
    assert "quarantined" in str(stmt).lower()
