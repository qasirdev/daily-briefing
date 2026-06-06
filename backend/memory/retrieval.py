"""Cross-layer memory retrieval helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import structlog

from backend.memory.audit import memory_audit_trail
from backend.memory.embeddings import embed_text_async
from backend.memory.episodic import EpisodicLessonRecord, EpisodicMemoryStore
from backend.memory.ingestion import validate_semantic_content
from backend.memory.procedural import ProceduralMemoryStore, ProceduralSkillRecord
from backend.memory.semantic import SemanticMemoryRecord, SemanticMemoryStore
from backend.metrics import record_memory_read, record_semantic_search_duration
from backend.settings import Settings, get_settings

logger = structlog.get_logger()

_default_store = SemanticMemoryStore()
_default_procedural = ProceduralMemoryStore()
_default_episodic = EpisodicMemoryStore()


@dataclass(frozen=True)
class AgentMemoryContext:
    """Combined memory context across CoALA layers."""

    semantic: tuple[SemanticMemoryRecord, ...]
    procedural: tuple[ProceduralSkillRecord, ...]
    episodic: tuple[EpisodicLessonRecord, ...]

    def to_payload(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "semantic_memory": format_semantic_context(list(self.semantic)),
            "procedural_skills": format_procedural_context(list(self.procedural)),
            "episodic_lessons": format_episodic_context(list(self.episodic)),
        }


def build_focus_retrieval_query(
    *,
    tasks: list[dict[str, object]],
    events: list[dict[str, object]],
    working_context: list[str] | tuple[str, ...] | None = None,
) -> str:
    """Build a retrieval query from working memory context and current MCP data."""
    parts: list[str] = []
    if working_context:
        parts.extend(str(item) for item in working_context[-3:] if str(item).strip())
    for task in tasks[:5]:
        title = task.get("title") or task.get("name") or task.get("summary")
        if title:
            parts.append(str(title))
    for event in events[:5]:
        summary = event.get("summary") or event.get("title") or event.get("name")
        if summary:
            parts.append(str(summary))
    if parts:
        return " | ".join(parts)
    return "daily briefing focus plan"


def format_semantic_context(records: list[SemanticMemoryRecord]) -> list[dict[str, Any]]:
    """Serialize semantic hits for agent user payloads."""
    return [
        {
            "content": record.content,
            "source_type": record.source_type,
            "source_id": record.source_id,
            "similarity": round(record.similarity, 4),
        }
        for record in records
    ]


def format_episodic_context(records: list[EpisodicLessonRecord]) -> list[dict[str, Any]]:
    """Serialize episodic lessons for agent user payloads."""
    return [
        {
            "lesson_type": record.lesson_type,
            "summary": record.summary,
            "session_id": record.session_id,
            "version": record.version,
        }
        for record in records
    ]


def format_procedural_context(records: list[ProceduralSkillRecord]) -> list[dict[str, Any]]:
    """Serialize procedural skills for agent user payloads."""
    return [
        {
            "skill_key": record.skill_key,
            "name": record.name,
            "steps": list(record.definition.steps),
            "tools": list(record.definition.tools),
            "success_criteria": record.definition.success_criteria,
            "success_count": record.success_count,
        }
        for record in records
    ]


async def retrieve_semantic_context(
    *,
    user_id: str,
    query_text: str,
    trace_id: str,
    agent_id: str,
    request_id: str = "",
    store: SemanticMemoryStore | None = None,
    settings: Settings | None = None,
    working_context: list[str] | tuple[str, ...] | None = None,
) -> list[SemanticMemoryRecord]:
    """Retrieve top-k semantic memories and record audit + metrics."""
    resolved_settings = settings or get_settings()
    if not resolved_settings.enable_semantic_memory_retrieval or not user_id:
        return []

    resolved_store = store or _default_store
    query = query_text.strip()
    if working_context and not query:
        query = build_focus_retrieval_query(tasks=[], events=[], working_context=working_context)
    if not query:
        return []

    embedding = await embed_text_async(query, resolved_settings)
    start = time.perf_counter()
    try:
        records = await resolved_store.search_similar(
            user_id=user_id,
            embedding=embedding,
            top_k=resolved_settings.semantic_memory_search_top_k,
        )
    except Exception as exc:
        logger.warning(
            "semantic_memory_retrieval_failed",
            trace_id=trace_id,
            user_id=user_id,
            agent_id=agent_id,
            error=str(exc),
        )
        return []

    duration_ms = (time.perf_counter() - start) * 1000.0
    record_semantic_search_duration(duration_ms=duration_ms, agent_id=agent_id)

    safe_records: list[SemanticMemoryRecord] = []
    for record in records:
        validation = validate_semantic_content(
            record.content,
            trace_id=trace_id,
            source=f"semantic_retrieval:{agent_id}",
        )
        if validation.accepted:
            safe_records.append(record)
        else:
            logger.warning(
                "semantic_memory_retrieval_blocked",
                trace_id=trace_id,
                user_id=user_id,
                agent_id=agent_id,
                memory_id=str(record.id),
                matched_pattern=validation.matched_pattern,
            )

    records = safe_records
    memory_audit_trail.log_read(
        trace_id=trace_id,
        request_id=request_id,
        user_id=user_id,
        agent_id=agent_id,
        memory_layer="semantic",
        operation="search",
        result_count=len(records),
        query_summary=query[:200],
    )
    record_memory_read(memory_layer="semantic", agent_id=agent_id, count=len(records))
    return records


async def retrieve_procedural_skills(
    *,
    user_id: str,
    agent_id: str,
    trace_id: str,
    request_id: str = "",
    store: ProceduralMemoryStore | None = None,
    settings: Settings | None = None,
) -> list[ProceduralSkillRecord]:
    """Retrieve access-controlled procedural skills for an agent."""
    resolved_settings = settings or get_settings()
    if not resolved_settings.enable_procedural_memory or not user_id:
        return []

    resolved_store = store or _default_procedural
    try:
        records = await resolved_store.list_skills_for_agent(
            user_id=user_id,
            requesting_agent_id=agent_id,
        )
    except Exception as exc:
        logger.warning(
            "procedural_memory_retrieval_failed",
            trace_id=trace_id,
            user_id=user_id,
            agent_id=agent_id,
            error=str(exc),
        )
        return []

    memory_audit_trail.log_read(
        trace_id=trace_id,
        request_id=request_id,
        user_id=user_id,
        agent_id=agent_id,
        memory_layer="procedural",
        operation="list",
        result_count=len(records),
    )
    record_memory_read(memory_layer="procedural", agent_id=agent_id, count=len(records))
    return records


async def retrieve_episodic_lessons(
    *,
    user_id: str,
    agent_id: str,
    trace_id: str,
    request_id: str = "",
    store: EpisodicMemoryStore | None = None,
    settings: Settings | None = None,
) -> list[EpisodicLessonRecord]:
    """Retrieve recent episodic lessons for an agent."""
    resolved_settings = settings or get_settings()
    if not resolved_settings.enable_episodic_memory or not user_id:
        return []

    resolved_store = store or _default_episodic
    try:
        records = await resolved_store.get_recent_lessons(user_id=user_id)
    except Exception as exc:
        logger.warning(
            "episodic_memory_retrieval_failed",
            trace_id=trace_id,
            user_id=user_id,
            agent_id=agent_id,
            error=str(exc),
        )
        return []

    memory_audit_trail.log_read(
        trace_id=trace_id,
        request_id=request_id,
        user_id=user_id,
        agent_id=agent_id,
        memory_layer="episodic",
        operation="list",
        result_count=len(records),
    )
    record_memory_read(memory_layer="episodic", agent_id=agent_id, count=len(records))
    return records


async def retrieve_agent_memory(
    *,
    user_id: str,
    agent_id: str,
    trace_id: str,
    request_id: str = "",
    query_text: str = "",
    working_context: list[str] | tuple[str, ...] | None = None,
    tasks: list[dict[str, object]] | None = None,
    events: list[dict[str, object]] | None = None,
    settings: Settings | None = None,
) -> AgentMemoryContext:
    """Retrieve semantic, procedural, and episodic context for an agent."""
    resolved_query = query_text.strip()
    if not resolved_query:
        resolved_query = build_focus_retrieval_query(
            tasks=tasks or [],
            events=events or [],
            working_context=working_context,
        )

    semantic = await retrieve_semantic_context(
        user_id=user_id,
        query_text=resolved_query,
        trace_id=trace_id,
        agent_id=agent_id,
        request_id=request_id,
        settings=settings,
        working_context=working_context,
    )
    procedural = await retrieve_procedural_skills(
        user_id=user_id,
        agent_id=agent_id,
        trace_id=trace_id,
        request_id=request_id,
        settings=settings,
    )
    episodic = await retrieve_episodic_lessons(
        user_id=user_id,
        agent_id=agent_id,
        trace_id=trace_id,
        request_id=request_id,
        settings=settings,
    )
    return AgentMemoryContext(
        semantic=tuple(semantic),
        procedural=tuple(procedural),
        episodic=tuple(episodic),
    )
