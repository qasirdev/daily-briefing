"""Tests for episodic memory store."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.memory.consolidation import distill_working_snippets
from backend.memory.episodic import EpisodicMemoryStore
from backend.settings import Settings


@pytest.mark.asyncio
async def test_store_lesson_persists_row() -> None:
    store = EpisodicMemoryStore()
    mock_session = AsyncMock()

    class _SessionContext:
        async def __aenter__(self) -> AsyncMock:
            return mock_session

        async def __aexit__(self, *args: object) -> None:
            return None

    with patch("backend.memory.episodic.session_scope", return_value=_SessionContext()):
        lesson_id = await store.store_lesson(
            user_id="user-1",
            session_id="req-abc",
            lesson_type="session_summary",
            summary="Focus plan approved → critic passed",
        )

    assert isinstance(lesson_id, uuid.UUID)
    mock_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_get_recent_lessons_excludes_superseded() -> None:
    store = EpisodicMemoryStore(Settings(episodic_memory_top_k=5))
    active = MagicMock()
    active.id = uuid.uuid4()
    active.user_id = "user-1"
    active.session_id = "req-1"
    active.lesson_type = "session_summary"
    active.summary = "Active lesson"
    active.version = 2
    active.superseded_by = None
    active.metadata_ = {}
    active.created_at = datetime.now(UTC)

    superseded = MagicMock()
    superseded.id = uuid.uuid4()
    superseded.user_id = "user-1"
    superseded.session_id = "req-0"
    superseded.lesson_type = "session_summary"
    superseded.summary = "Old lesson"
    superseded.version = 1
    superseded.superseded_by = uuid.uuid4()
    superseded.metadata_ = {}
    superseded.created_at = datetime.now(UTC)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [active, superseded]
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    class _SessionContext:
        async def __aenter__(self) -> AsyncMock:
            return mock_session

        async def __aexit__(self, *args: object) -> None:
            return None

    with patch("backend.memory.episodic.session_scope", return_value=_SessionContext()):
        lessons = await store.get_recent_lessons(user_id="user-1")

    assert len(lessons) == 1
    assert lessons[0].summary == "Active lesson"


def test_distill_working_snippets_joins_context() -> None:
    result = distill_working_snippets(["Focus plan", "Critic approved", ""])
    assert result == "Focus plan → Critic approved"
