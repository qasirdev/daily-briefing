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
MemoryMutationAction = Literal["quarantine", "restore", "delete"]


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


class MemoryMutationAuditEntry(BaseModel):
    """Structured audit record for quarantine workflow actions."""

    model_config = ConfigDict(strict=True, frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    trace_id: str = Field(..., min_length=32, max_length=64)
    user_id: str = Field(..., min_length=1, max_length=64)
    memory_layer: MemoryLayer
    action: MemoryMutationAction
    memory_id: str = Field(..., min_length=1, max_length=64)
    reason: str = Field(default="", max_length=200)
    actor: str = Field(default="system", max_length=64)


class MemoryAuditTrail:
    """In-process audit trail for memory reads (tests and structured logs)."""

    def __init__(self) -> None:
        self._entries: list[MemoryReadAuditEntry] = []
        self._mutations: list[MemoryMutationAuditEntry] = []

    @property
    def entries(self) -> tuple[MemoryReadAuditEntry, ...]:
        return tuple(self._entries)

    @property
    def mutations(self) -> tuple[MemoryMutationAuditEntry, ...]:
        return tuple(self._mutations)

    def clear(self) -> None:
        self._entries.clear()
        self._mutations.clear()

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

    def log_mutation(
        self,
        *,
        trace_id: str,
        user_id: str,
        memory_layer: MemoryLayer,
        action: MemoryMutationAction,
        memory_id: str,
        reason: str = "",
        actor: str = "system",
    ) -> MemoryMutationAuditEntry:
        """Record a quarantine workflow action and emit a structured audit log."""
        entry = MemoryMutationAuditEntry(
            trace_id=trace_id,
            user_id=user_id,
            memory_layer=memory_layer,
            action=action,
            memory_id=memory_id,
            reason=reason[:200],
            actor=actor,
        )
        self._mutations.append(entry)
        logger.info(
            "memory_mutation_audit",
            audit_id=entry.id,
            trace_id=trace_id,
            user_id=user_id,
            memory_layer=memory_layer,
            action=action,
            memory_id=memory_id,
            reason=entry.reason,
            actor=actor,
        )
        return entry


memory_audit_trail = MemoryAuditTrail()
