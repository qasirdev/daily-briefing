"""Per-action authorization tests (Gaps #52, #128)."""

from __future__ import annotations

import pytest

from backend.consent.store import ConsentStore
from backend.schemas.consent import ConsentGrantRequest
from backend.security.per_action_authz import ActionRequest, PerActionAuthorizer
from backend.security.policy_engine import PolicyDeniedError, PolicyEngine


@pytest.fixture
def consent() -> ConsentStore:
    store = ConsentStore()
    store.grant(
        ConsentGrantRequest(
            user_id="user-1",
            service="google_calendar",
            scope=["calendar.readonly"],
            agent_id="calendar",
            ttl_hours=4,
        ),
    )
    return store


@pytest.fixture
def authorizer(consent: ConsentStore) -> PerActionAuthorizer:
    return PerActionAuthorizer(PolicyEngine(consent=consent))


def test_authorize_allows_valid_credential_issue(authorizer: PerActionAuthorizer) -> None:
    decision = authorizer.authorize(
        ActionRequest(
            user_id="user-1",
            agent_id="calendar",
            service="google_calendar",
            action="credential_issue",
            intent="read_events",
        ),
    )
    assert decision.allowed is True


def test_authorize_denies_missing_consent(authorizer: PerActionAuthorizer) -> None:
    decision = authorizer.authorize(
        ActionRequest(
            user_id="user-2",
            agent_id="calendar",
            service="google_calendar",
            action="credential_issue",
            intent="read_events",
        ),
    )
    assert decision.allowed is False
    assert "consent" in decision.reason


def test_authorize_denies_agent_mismatch(authorizer: PerActionAuthorizer) -> None:
    decision = authorizer.authorize(
        ActionRequest(
            user_id="user-1",
            agent_id="task",
            service="google_calendar",
            action="credential_issue",
            intent="read_events",
        ),
    )
    assert decision.allowed is False
    assert "agent_mismatch" in decision.reason


def test_authorize_denies_write_without_scope(consent: ConsentStore) -> None:
    authorizer = PerActionAuthorizer(PolicyEngine(consent=consent))
    decision = authorizer.authorize(
        ActionRequest(
            user_id="user-1",
            agent_id="calendar",
            service="google_calendar",
            action="data_write",
            scope=["calendar.write"],
        ),
    )
    assert decision.allowed is False
    assert "write_scope" in decision.reason


def test_authorize_or_raise_raises_on_deny(authorizer: PerActionAuthorizer) -> None:
    with pytest.raises(PolicyDeniedError):
        authorizer.authorize_or_raise(
            ActionRequest(
                user_id="unknown",
                agent_id="calendar",
                service="google_calendar",
                action="mcp_tool",
                scope=["calendar.readonly"],
            ),
        )


def test_revoked_consent_denied_immediately(consent: ConsentStore) -> None:
    record = consent.grant(
        ConsentGrantRequest(
            user_id="user-3",
            service="postgres_mcp",
            scope=["tasks.read"],
            agent_id="task",
            ttl_hours=4,
        ),
    )
    authorizer = PerActionAuthorizer(PolicyEngine(consent=consent))
    assert authorizer.authorize(
        ActionRequest(
            user_id="user-3",
            agent_id="task",
            service="postgres_mcp",
            action="data_read",
            scope=["tasks.read"],
        ),
    ).allowed

    consent.revoke(record.id)
    decision = authorizer.authorize(
        ActionRequest(
            user_id="user-3",
            agent_id="task",
            service="postgres_mcp",
            action="data_read",
            scope=["tasks.read"],
        ),
    )
    assert decision.allowed is False


def test_empty_user_id_denied(authorizer: PerActionAuthorizer) -> None:
    decision = authorizer.authorize(
        ActionRequest(
            user_id="   ",
            agent_id="calendar",
            service="google_calendar",
            action="credential_issue",
            intent="read_events",
        ),
    )
    assert decision.allowed is False
