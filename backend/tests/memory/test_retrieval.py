"""Tests for cross-layer memory retrieval."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.memory.audit import memory_audit_trail
from backend.memory.retrieval import (
    build_focus_retrieval_query,
    retrieve_semantic_context,
)
from backend.memory.semantic import SemanticMemoryRecord
from backend.settings import Settings

TRACE_ID = "b" * 32


def test_build_focus_retrieval_query_merges_working_and_mcp_data() -> None:
    query = build_focus_retrieval_query(
        tasks=[{"title": "Q2 report"}],
        events=[{"summary": "Sprint Review"}],
        working_context=["Prior critic feedback"],
    )
    assert "Prior critic feedback" in query
    assert "Q2 report" in query
    assert "Sprint Review" in query


@pytest.mark.asyncio
async def test_retrieve_semantic_context_skips_when_disabled() -> None:
    memory_audit_trail.clear()
    records = await retrieve_semantic_context(
        user_id="user-1",
        query_text="daily briefing",
        trace_id=TRACE_ID,
        agent_id="focus",
        settings=Settings(enable_semantic_memory_retrieval=False),
    )
    assert records == []
    assert memory_audit_trail.entries == ()


@pytest.mark.asyncio
async def test_cross_layer_working_to_semantic_retrieval() -> None:
    memory_audit_trail.clear()
    created_at = datetime.now(UTC)
    mock_records = [
        SemanticMemoryRecord(
            id=uuid.uuid4(),
            user_id="user-1",
            content="Previous focus on Q2 report",
            source_type="briefing",
            source_id="brief-1",
            similarity=0.88,
            created_at=created_at,
        ),
    ]
    mock_store = AsyncMock()
    mock_store.search_similar = AsyncMock(return_value=mock_records)

    records = await retrieve_semantic_context(
        user_id="user-1",
        query_text="",
        trace_id=TRACE_ID,
        agent_id="focus",
        request_id="req-1",
        store=mock_store,
        settings=Settings(
            semantic_memory_embedding_dim=8,
            semantic_memory_search_top_k=3,
        ),
        working_context=["Q2 report deep work"],
    )

    assert len(records) == 1
    mock_store.search_similar.assert_awaited_once()
    semantic_audits = [
        entry for entry in memory_audit_trail.entries if entry.memory_layer == "semantic"
    ]
    assert len(semantic_audits) == 1
    assert semantic_audits[0].result_count == 1


@pytest.mark.asyncio
async def test_retrieve_semantic_context_records_metrics() -> None:
    memory_audit_trail.clear()
    mock_store = AsyncMock()
    mock_store.search_similar = AsyncMock(return_value=[])

    with patch("backend.memory.retrieval.record_semantic_search_duration") as mock_duration:
        with patch("backend.memory.retrieval.record_memory_read") as mock_reads:
            await retrieve_semantic_context(
                user_id="user-1",
                query_text="standup prep",
                trace_id=TRACE_ID,
                agent_id="focus",
                store=mock_store,
            )

    mock_duration.assert_called_once()
    mock_reads.assert_called_once_with(memory_layer="semantic", agent_id="focus", count=0)
