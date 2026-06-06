"""Cross-layer memory retrieval helpers."""

from __future__ import annotations

import time
from typing import Any

import structlog

from backend.memory.audit import memory_audit_trail
from backend.memory.embeddings import embed_text
from backend.memory.semantic import SemanticMemoryRecord, SemanticMemoryStore
from backend.metrics import record_memory_read, record_semantic_search_duration
from backend.settings import Settings, get_settings

logger = structlog.get_logger()

_default_store = SemanticMemoryStore()


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

    embedding = embed_text(query, resolved_settings)
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
