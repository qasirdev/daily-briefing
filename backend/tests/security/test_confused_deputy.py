"""Confused deputy prevention tests (Gap #118)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.security.delegation import DelegationContext, issue_delegation, validate_delegation


def test_issue_delegation_creates_short_lived_context() -> None:
    context = issue_delegation(
        user_id="user-1",
        session_id="sess-1",
        agent_id="calendar",
        intent="read_events",
        permissions=("calendar:read",),
        parent_trace_id="a" * 32,
        ttl_seconds=900,
    )
    assert context.user_id == "user-1"
    assert context.intent == "read_events"
    assert context.expires_at > context.issued_at
    assert "user_id" in context.to_token_payload()


def test_validate_delegation_rejects_expired_context() -> None:
    expired = DelegationContext(
        user_id="user-1",
        session_id="sess-1",
        agent_id="calendar",
        intent="read_events",
        permissions=("calendar:read",),
        issued_at=datetime.now(UTC) - timedelta(hours=1),
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
        parent_trace_id="b" * 32,
    )
    with pytest.raises(ValueError, match="expired"):
        validate_delegation(expired)


def test_validate_delegation_rejects_intent_mismatch() -> None:
    context = issue_delegation(
        user_id="user-1",
        session_id="sess-1",
        agent_id="task",
        intent="read_tasks",
        permissions=("tasks:read",),
        parent_trace_id="c" * 32,
    )
    with pytest.raises(ValueError, match="intent mismatch"):
        validate_delegation(context, required_intent="update_tasks")
