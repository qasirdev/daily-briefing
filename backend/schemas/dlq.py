"""Dead letter queue event schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.envelope import AgentResultEnvelope

DLQReason = Literal[
    "security_violation_detected",
    "max_retries_exceeded",
    "token_budget_exceeded",
    "mcp_timeout",
    "consent_expired",
    "circuit_breaker",
    "unexpected_error",
]

NON_RETRYABLE_REASONS = frozenset(
    {
        "security_violation_detected",
        "token_budget_exceeded",
    },
)

MAX_DLQ_RETRIES = 3


class DLQEvent(BaseModel):
    """Persisted dead letter queue record."""

    model_config = ConfigDict(strict=True)

    id: UUID = Field(default_factory=uuid4)
    request_id: str
    user_id: str
    agent_id: str
    reason: DLQReason
    envelope: AgentResultEnvelope | None = None
    trace_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    retried_at: datetime | None = None
    retry_count: int = Field(default=0, ge=0)


class DLQEventSummary(BaseModel):
    """List view of DLQ events."""

    model_config = ConfigDict(strict=True)

    id: UUID
    request_id: str
    user_id: str
    agent_id: str
    reason: DLQReason
    trace_id: str
    created_at: datetime
    retried_at: datetime | None
    retry_count: int


class DLQRetryResponse(BaseModel):
    """Response after attempting a DLQ retry."""

    model_config = ConfigDict(strict=True)

    event_id: UUID
    status: Literal["retry_started", "rejected"]
    message: str
