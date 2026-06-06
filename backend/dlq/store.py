"""In-memory DLQ store with optional Postgres persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import structlog

from backend.db.models import DLQEventRow
from backend.db.session import session_scope
from backend.dependencies import PostgresMCPProtocol
from backend.metrics import record_dlq_event
from backend.schemas.dlq import MAX_DLQ_RETRIES, NON_RETRYABLE_REASONS, DLQEvent
from backend.settings import get_settings

logger = structlog.get_logger()


class DLQStore:
    """Process-local DLQ with MCP persistence when available."""

    def __init__(self) -> None:
        self._events: dict[UUID, DLQEvent] = {}

    def add(self, event: DLQEvent) -> DLQEvent:
        self._events[event.id] = event
        record_dlq_event(reason=event.reason, agent_id=event.agent_id)
        return event

    async def _persist_sqlalchemy(self, stored: DLQEvent) -> None:
        row = DLQEventRow(
            id=stored.id,
            request_id=stored.request_id,
            user_id=stored.user_id,
            agent_id=stored.agent_id,
            reason=stored.reason,
            trace_id=stored.trace_id,
            retry_count=stored.retry_count,
            envelope=(stored.envelope.model_dump(mode="json") if stored.envelope else None),
            created_at=stored.created_at,
        )
        async with session_scope() as session:
            session.add(row)

    async def persist(
        self,
        event: DLQEvent,
        *,
        postgres: PostgresMCPProtocol | None = None,
    ) -> DLQEvent:
        stored = self.add(event)
        settings = get_settings()
        if "asyncpg" in settings.database_url:
            try:
                await self._persist_sqlalchemy(stored)
                return stored
            except Exception as exc:  # noqa: BLE001 — fall back to MCP when DB unavailable
                logger.error(
                    "dlq_sqlalchemy_persist_failed",
                    trace_id=event.trace_id,
                    event_id=str(event.id),
                    error=str(exc),
                )
        if postgres is not None:
            try:
                await postgres.insert(
                    table="dlq_events",
                    user_id=event.user_id,
                    data={
                        "id": str(stored.id),
                        "request_id": stored.request_id,
                        "user_id": stored.user_id,
                        "agent_id": stored.agent_id,
                        "reason": stored.reason,
                        "trace_id": stored.trace_id,
                        "retry_count": stored.retry_count,
                        "created_at": stored.created_at.isoformat(),
                        "envelope": (
                            stored.envelope.model_dump(mode="json") if stored.envelope else None
                        ),
                    },
                )
            except Exception as exc:  # noqa: BLE001 — DLQ insert must not crash graph
                logger.error(
                    "dlq_persist_failed",
                    trace_id=event.trace_id,
                    event_id=str(event.id),
                    error=str(exc),
                )
        return stored

    def list_events(self) -> list[DLQEvent]:
        return sorted(self._events.values(), key=lambda item: item.created_at, reverse=True)

    def get(self, event_id: UUID) -> DLQEvent | None:
        return self._events.get(event_id)

    def mark_retry(self, event_id: UUID) -> DLQEvent | None:
        event = self._events.get(event_id)
        if event is None:
            return None
        updated = event.model_copy(
            update={
                "retry_count": event.retry_count + 1,
                "retried_at": datetime.now(UTC),
            },
        )
        self._events[event_id] = updated
        return updated

    def can_retry(self, event: DLQEvent) -> tuple[bool, str]:
        if event.reason in NON_RETRYABLE_REASONS:
            return False, "Security violations and token budget events cannot be retried"
        if event.retry_count >= MAX_DLQ_RETRIES:
            return False, "Retry limit exceeded"
        return True, ""


dlq_store = DLQStore()
