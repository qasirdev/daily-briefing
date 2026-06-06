"""Audit trail for memory read operations."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

import structlog
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger()

MemoryLayer = Literal["semantic", "working", "procedural", "episodic"]
MemoryOperation = Literal["search", "get", "snapshot", "list"]


class MemoryReadAuditEntry(BaseModel):
    """Structured audit record for a memory read."""

    model_config = ConfigDict(strict=True, frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    trace_id: str = Field(..., min_length=32, max_length=64)
    request_id: str = Field(default="")
    user_id: str = Field(..., min_length=1, max_length=64)
    agent_id: str = Field(..., min_length=1, max_length=32)
    memory_layer: MemoryLayer
    operation: MemoryOperation
    result_count: int = Field(..., ge=0)
    query_summary: str = Field(default="", max_length=200)


class MemoryAuditTrail:
    """In-process audit trail for memory reads (tests and structured logs)."""

    def __init__(self) -> None:
        self._entries: list[MemoryReadAuditEntry] = []

    @property
    def entries(self) -> tuple[MemoryReadAuditEntry, ...]:
        return tuple(self._entries)

    def clear(self) -> None:
        self._entries.clear()

    def log_read(
        self,
        *,
        trace_id: str,
        user_id: str,
        agent_id: str,
        memory_layer: MemoryLayer,
        operation: MemoryOperation,
        result_count: int,
        request_id: str = "",
        query_summary: str = "",
    ) -> MemoryReadAuditEntry:
        """Record a memory read and emit a structured audit log."""
        entry = MemoryReadAuditEntry(
            trace_id=trace_id,
            request_id=request_id,
            user_id=user_id,
            agent_id=agent_id,
            memory_layer=memory_layer,
            operation=operation,
            result_count=result_count,
            query_summary=query_summary[:200],
        )
        self._entries.append(entry)
        logger.info(
            "memory_read_audit",
            audit_id=entry.id,
            trace_id=trace_id,
            request_id=request_id,
            user_id=user_id,
            agent_id=agent_id,
            memory_layer=memory_layer,
            operation=operation,
            result_count=result_count,
            query_summary=entry.query_summary,
        )
        return entry


memory_audit_trail = MemoryAuditTrail()
