"""Tests for cross-layer memory retrieval."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.memory.episodic import EpisodicLessonRecord
from backend.memory.procedural import ProceduralSkillDefinition, ProceduralSkillRecord
from backend.memory.retrieval import retrieve_agent_memory
from backend.memory.semantic import SemanticMemoryRecord
from backend.settings import Settings


@pytest.mark.asyncio
async def test_retrieve_agent_memory_combines_all_layers() -> None:
    memory_id = uuid.uuid4()
    created = datetime.now(UTC)
    semantic = [
        SemanticMemoryRecord(
            id=memory_id,
            user_id="user-1",
            content="Prior briefing",
            source_type="briefing",
            source_id="b1",
            similarity=0.9,
            created_at=created,
        ),
    ]
    procedural = [
        ProceduralSkillRecord(
            id=uuid.uuid4(),
            user_id="user-1",
            agent_id="focus",
            skill_key="plan",
            name="Plan",
            definition=ProceduralSkillDefinition(steps=("Step",)),
            allowed_agents=("focus",),
            success_count=1,
            last_used_at=None,
            created_at=created,
        ),
    ]
    episodic = [
        EpisodicLessonRecord(
            id=uuid.uuid4(),
            user_id="user-1",
            session_id="req-1",
            lesson_type="session_summary",
            summary="Previous session lesson",
            version=1,
            superseded_by=None,
            metadata={},
            created_at=created,
        ),
    ]

    with (
        patch(
            "backend.memory.retrieval.retrieve_semantic_context",
            new=AsyncMock(return_value=semantic),
        ),
        patch(
            "backend.memory.retrieval.retrieve_procedural_skills",
            new=AsyncMock(return_value=procedural),
        ),
        patch(
            "backend.memory.retrieval.retrieve_episodic_lessons",
            new=AsyncMock(return_value=episodic),
        ),
    ):
        context = await retrieve_agent_memory(
            user_id="user-1",
            agent_id="focus",
            trace_id="a" * 32,
            query_text="daily plan",
            settings=Settings(),
        )

    assert len(context.semantic) == 1
    assert len(context.procedural) == 1
    assert len(context.episodic) == 1
    payload = context.to_payload()
    assert "semantic_memory" in payload
    assert "procedural_skills" in payload
    assert "episodic_lessons" in payload


@pytest.mark.asyncio
async def test_retrieve_agent_memory_respects_disabled_flags() -> None:
    settings = Settings(
        enable_semantic_memory_retrieval=False,
        enable_procedural_memory=False,
        enable_episodic_memory=False,
    )
    context = await retrieve_agent_memory(
        user_id="user-1",
        agent_id="focus",
        trace_id="a" * 32,
        query_text="test",
        settings=settings,
    )
    assert context.semantic == ()
    assert context.procedural == ()
    assert context.episodic == ()
