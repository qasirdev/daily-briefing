"""Tests for semantic memory store."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.memory.semantic import SemanticMemoryStore
from backend.settings import Settings


@pytest.mark.asyncio
async def test_store_rejects_wrong_embedding_dimension() -> None:
    store = SemanticMemoryStore(Settings(semantic_memory_embedding_dim=4))
    with pytest.raises(ValueError, match="Embedding dimension mismatch"):
        await store.store(
            user_id="user-1",
            content="hello",
            embedding=[0.1, 0.2],
            source_type="briefing",
        )


@pytest.mark.asyncio
async def test_store_persists_row() -> None:
    store = SemanticMemoryStore(Settings(semantic_memory_embedding_dim=4))
    embedding = [1.0, 0.0, 0.0, 0.0]
    mock_session = AsyncMock()

    class _SessionContext:
        async def __aenter__(self) -> AsyncMock:
            return mock_session

        async def __aexit__(self, *args: object) -> None:
            return None

    with patch("backend.memory.semantic.session_scope", return_value=_SessionContext()):
        memory_id = await store.store(
            user_id="user-1",
            content="Past briefing summary",
            embedding=embedding,
            source_type="briefing",
            source_id="brief-1",
        )

    assert isinstance(memory_id, uuid.UUID)
    mock_session.add.assert_called_once()
    mock_session.execute.assert_awaited()


@pytest.mark.asyncio
async def test_search_similar_maps_rows() -> None:
    store = SemanticMemoryStore(Settings(semantic_memory_embedding_dim=4))
    memory_id = uuid.uuid4()
    created_at = datetime.now(UTC)
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = [
        {
            "id": memory_id,
            "user_id": "user-1",
            "content": "Prior focus on Q2 report",
            "source_type": "briefing",
            "source_id": "brief-1",
            "created_at": created_at,
            "similarity": 0.92,
        },
    ]
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    class _SessionContext:
        async def __aenter__(self) -> AsyncMock:
            return mock_session

        async def __aexit__(self, *args: object) -> None:
            return None

    with patch("backend.memory.semantic.session_scope", return_value=_SessionContext()):
        results = await store.search_similar(
            user_id="user-1",
            embedding=[1.0, 0.0, 0.0, 0.0],
            top_k=3,
        )

    assert len(results) == 1
    assert results[0].id == memory_id
    assert results[0].similarity == 0.92
    assert results[0].content == "Prior focus on Q2 report"
