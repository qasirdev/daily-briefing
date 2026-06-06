"""Tests for procedural memory store."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.memory.procedural import (
    ProceduralMemoryStore,
    ProceduralSkillDefinition,
)
from backend.settings import Settings


@pytest.mark.asyncio
async def test_list_skills_filters_by_allowed_agents() -> None:
    store = ProceduralMemoryStore(Settings(procedural_memory_top_k=5))
    allowed_row = MagicMock()
    allowed_row.id = uuid.uuid4()
    allowed_row.user_id = "user-1"
    allowed_row.agent_id = "focus"
    allowed_row.skill_key = "plan_morning"
    allowed_row.name = "Morning planning"
    allowed_row.definition = {
        "steps": ["Review tasks", "Block calendar"],
        "tools": [],
        "success_criteria": "Plan generated",
    }
    allowed_row.allowed_agents = ["focus", "orchestrator"]
    allowed_row.success_count = 3
    allowed_row.last_used_at = datetime.now(UTC)
    allowed_row.created_at = datetime.now(UTC)

    denied_row = MagicMock()
    denied_row.id = uuid.uuid4()
    denied_row.user_id = "user-1"
    denied_row.agent_id = "task"
    denied_row.skill_key = "fetch_only"
    denied_row.name = "Task fetch"
    denied_row.definition = {"steps": ["Query DB"], "tools": ["postgres"], "success_criteria": ""}
    denied_row.allowed_agents = ["task"]
    denied_row.success_count = 10
    denied_row.last_used_at = None
    denied_row.created_at = datetime.now(UTC)

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [denied_row, allowed_row]
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    class _SessionContext:
        async def __aenter__(self) -> AsyncMock:
            return mock_session

        async def __aexit__(self, *args: object) -> None:
            return None

    with patch("backend.memory.procedural.session_scope", return_value=_SessionContext()):
        skills = await store.list_skills_for_agent(
            user_id="user-1",
            requesting_agent_id="focus",
        )

    assert len(skills) == 1
    assert skills[0].skill_key == "plan_morning"
    assert skills[0].definition.steps == ("Review tasks", "Block calendar")


@pytest.mark.asyncio
async def test_register_skill_persists_row() -> None:
    store = ProceduralMemoryStore()
    mock_session = AsyncMock()

    class _SessionContext:
        async def __aenter__(self) -> AsyncMock:
            return mock_session

        async def __aexit__(self, *args: object) -> None:
            return None

    definition = ProceduralSkillDefinition(
        steps=("Step one",),
        tools=("postgres",),
        success_criteria="Done",
    )
    with patch("backend.memory.procedural.session_scope", return_value=_SessionContext()):
        skill_id = await store.register_skill(
            user_id="user-1",
            agent_id="focus",
            skill_key="test_skill",
            name="Test Skill",
            definition=definition,
            allowed_agents=("focus",),
        )

    assert isinstance(skill_id, uuid.UUID)
    mock_session.add.assert_called_once()
