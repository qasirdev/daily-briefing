"""Procedural memory store — learned workflows and skill definitions (CoALA layer 3)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import ProceduralMemoryRow
from backend.db.session import session_scope
from backend.settings import Settings, get_settings

logger = structlog.get_logger()


class ProceduralSkillDefinition(BaseModel):
    """JSON skill definition with progressive disclosure metadata."""

    model_config = ConfigDict(strict=True, frozen=True)

    steps: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    success_criteria: str = ""


class ProceduralSkillRecord(BaseModel):
    """Retrieved procedural skill with access metadata."""

    model_config = ConfigDict(strict=True, frozen=True)

    id: uuid.UUID
    user_id: str = Field(..., min_length=1, max_length=64)
    agent_id: str = Field(..., min_length=1, max_length=50)
    skill_key: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=200)
    definition: ProceduralSkillDefinition
    allowed_agents: tuple[str, ...] = ()
    success_count: int = Field(..., ge=0)
    last_used_at: datetime | None = None
    created_at: datetime


def _parse_definition(raw: dict[str, object]) -> ProceduralSkillDefinition:
    steps_raw = raw.get("steps", [])
    tools_raw = raw.get("tools", [])
    steps = tuple(str(item) for item in steps_raw) if isinstance(steps_raw, list) else ()
    tools = tuple(str(item) for item in tools_raw) if isinstance(tools_raw, list) else ()
    criteria = raw.get("success_criteria", "")
    return ProceduralSkillDefinition(
        steps=steps,
        tools=tools,
        success_criteria=str(criteria) if criteria else "",
    )


def _row_to_record(row: ProceduralMemoryRow) -> ProceduralSkillRecord:
    allowed = tuple(str(a) for a in row.allowed_agents) if row.allowed_agents else ()
    return ProceduralSkillRecord(
        id=row.id,
        user_id=row.user_id,
        agent_id=row.agent_id,
        skill_key=row.skill_key,
        name=row.name,
        definition=_parse_definition(row.definition),
        allowed_agents=allowed,
        success_count=row.success_count,
        last_used_at=row.last_used_at,
        created_at=row.created_at,
    )


class ProceduralMemoryStore:
    """Persist and retrieve procedural skills with agent access control."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def _set_user_context(self, session: AsyncSession, user_id: str) -> None:
        await session.execute(
            text("SELECT set_config('app.user_id', :user_id, true)"),
            {"user_id": user_id},
        )

    async def register_skill(
        self,
        *,
        user_id: str,
        agent_id: str,
        skill_key: str,
        name: str,
        definition: ProceduralSkillDefinition,
        allowed_agents: tuple[str, ...] | list[str] | None = None,
    ) -> uuid.UUID:
        """Register or replace a procedural skill for a user."""
        skill_id = uuid.uuid4()
        allowed = list(allowed_agents or (agent_id,))
        definition_payload: dict[str, Any] = {
            "steps": list(definition.steps),
            "tools": list(definition.tools),
            "success_criteria": definition.success_criteria,
        }
        row = ProceduralMemoryRow(
            id=skill_id,
            user_id=user_id,
            agent_id=agent_id,
            skill_key=skill_key,
            name=name,
            definition=definition_payload,
            allowed_agents=allowed,
            success_count=0,
            last_used_at=None,
            created_at=datetime.now(UTC),
        )
        async with session_scope() as session:
            await self._set_user_context(session, user_id)
            session.add(row)
        logger.info(
            "procedural_skill_registered",
            user_id=user_id,
            agent_id=agent_id,
            skill_key=skill_key,
        )
        return skill_id

    async def list_skills_for_agent(
        self,
        *,
        user_id: str,
        requesting_agent_id: str,
        top_k: int | None = None,
    ) -> list[ProceduralSkillRecord]:
        """Return skills the requesting agent is permitted to use."""
        limit = top_k or self._settings.procedural_memory_top_k
        async with session_scope() as session:
            await self._set_user_context(session, user_id)
            stmt = (
                select(ProceduralMemoryRow)
                .where(ProceduralMemoryRow.user_id == user_id)
                .order_by(
                    ProceduralMemoryRow.success_count.desc(),
                    ProceduralMemoryRow.last_used_at.desc().nullslast(),
                )
                .limit(limit * 3)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

        records = [_row_to_record(row) for row in rows]
        filtered = [
            record
            for record in records
            if requesting_agent_id in record.allowed_agents
            or record.agent_id == requesting_agent_id
        ]
        return filtered[:limit]

    async def record_success(
        self,
        *,
        user_id: str,
        skill_id: uuid.UUID,
    ) -> None:
        """Increment success count when a skill workflow completes."""
        async with session_scope() as session:
            await self._set_user_context(session, user_id)
            await session.execute(
                update(ProceduralMemoryRow)
                .where(
                    ProceduralMemoryRow.id == skill_id,
                    ProceduralMemoryRow.user_id == user_id,
                )
                .values(
                    success_count=ProceduralMemoryRow.success_count + 1,
                    last_used_at=datetime.now(UTC),
                ),
            )
