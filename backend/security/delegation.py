"""Delegation token framework for confused-deputy prevention (Gap #118)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

import structlog

from backend.security.audit import audit_log_writer

logger = structlog.get_logger()

DEFAULT_DELEGATION_TTL_SECONDS = 900  # 15 minutes per spec


@dataclass(frozen=True)
class DelegationContext:
    """User-scoped delegation token propagated through the agent chain."""

    user_id: str
    session_id: str
    agent_id: str
    intent: Literal["read_events", "read_tasks", "update_tasks"]
    permissions: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime
    parent_trace_id: str

    def is_expired(self, *, now: datetime | None = None) -> bool:
        reference = now or datetime.now(UTC)
        return reference >= self.expires_at

    def to_token_payload(self) -> dict[str, object]:
        return {
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "intent": self.intent,
            "expires": int(self.expires_at.timestamp()),
        }


def issue_delegation(
    *,
    user_id: str,
    session_id: str,
    agent_id: str,
    intent: Literal["read_events", "read_tasks", "update_tasks"],
    permissions: tuple[str, ...],
    parent_trace_id: str,
    ttl_seconds: int = DEFAULT_DELEGATION_TTL_SECONDS,
) -> DelegationContext:
    """Issue a short-lived delegation context on behalf of the user."""
    issued_at = datetime.now(UTC)
    context = DelegationContext(
        user_id=user_id,
        session_id=session_id,
        agent_id=agent_id,
        intent=intent,
        permissions=permissions,
        issued_at=issued_at,
        expires_at=issued_at + timedelta(seconds=ttl_seconds),
        parent_trace_id=parent_trace_id,
    )
    audit_log_writer.append(
        event_type="delegation_created",
        actor_id=user_id,
        resource=f"agent:{agent_id}",
        payload={
            "intent": intent,
            "permissions": list(permissions),
            "expires_at": context.expires_at.isoformat(),
            "trace_id": parent_trace_id,
        },
    )
    logger.info(
        "delegation_issued",
        user_id=user_id,
        agent_id=agent_id,
        intent=intent,
        trace_id=parent_trace_id,
    )
    return context


def validate_delegation(
    context: DelegationContext,
    *,
    required_intent: Literal["read_events", "read_tasks", "update_tasks"] | None = None,
    required_permission: str | None = None,
) -> None:
    """Raise ValueError when delegation is expired or insufficient for the action."""
    if context.is_expired():
        msg = f"Delegation expired for agent {context.agent_id}"
        raise ValueError(msg)
    if required_intent is not None and context.intent != required_intent:
        msg = f"Delegation intent mismatch: expected {required_intent}, got {context.intent}"
        raise ValueError(msg)
    if required_permission is not None and required_permission not in context.permissions:
        msg = f"Delegation missing permission: {required_permission}"
        raise ValueError(msg)
