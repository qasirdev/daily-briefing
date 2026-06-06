"""Tests for JIT credential broker (DB-124)."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from backend.consent.store import ConsentStore
from backend.observability.metrics import CREDENTIAL_ISSUANCE_TOTAL
from backend.schemas.consent import ConsentGrantRequest
from backend.security.audit import AuditLogWriter
from backend.security.vault import (
    CredentialBroker,
    CredentialBrokerError,
    CredentialDeniedError,
)
from backend.settings import Settings


class FakeTokenExchanger:
    async def exchange_google_refresh_token(
        self,
        *,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> dict[str, Any]:
        del client_id, client_secret
        if refresh_token == "bad-token":
            raise CredentialBrokerError("exchange failed")
        return {
            "access_token": "ya29.access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }


@pytest.fixture
def consent() -> ConsentStore:
    store = ConsentStore()
    store.grant(
        ConsentGrantRequest(
            user_id="user-1",
            service="google_calendar",
            scope=["calendar.readonly"],
            ttl_hours=4,
        ),
    )
    return store


@pytest.fixture
def broker(consent: ConsentStore) -> CredentialBroker:
    settings = Settings(
        google_refresh_token="refresh-token",
        google_client_id="client-id",
        google_client_secret="client-secret",
        vault_mode="memory",
        credential_ttl_seconds=900,
    )
    return CredentialBroker(
        settings,
        consent=consent,
        audit=AuditLogWriter(),
        token_exchanger=FakeTokenExchanger(),
    )


async def test_broker_returns_credential_within_ttl(broker: CredentialBroker) -> None:
    credential = await broker.get_credential("user-1", "google_calendar", "read_events")
    assert credential.access_token == "ya29.access-token"
    assert credential.expires_at > datetime.now(UTC)


async def test_broker_cache_hit_within_ttl(broker: CredentialBroker) -> None:
    first = await broker.get_credential("user-1", "google_calendar", "read_events")
    second = await broker.get_credential("user-1", "google_calendar", "read_events")
    assert first.access_token == second.access_token
    assert len(broker._audit.entries) == 1


async def test_broker_denies_without_consent() -> None:
    broker = CredentialBroker(
        Settings(google_refresh_token="refresh-token", vault_mode="memory"),
        consent=ConsentStore(),
        audit=AuditLogWriter(),
        token_exchanger=FakeTokenExchanger(),
    )
    with pytest.raises(CredentialDeniedError):
        await broker.get_credential("user-2", "google_calendar", "read_events")


async def test_broker_rejects_non_positive_ttl(broker: CredentialBroker) -> None:
    with pytest.raises(ValueError, match="ttl_seconds must be positive"):
        await broker.get_credential(
            "user-1",
            "google_calendar",
            "read_events",
            ttl_seconds=0,
        )


async def test_broker_raises_when_refresh_token_missing() -> None:
    broker = CredentialBroker(
        Settings(google_refresh_token="", vault_mode="memory"),
        consent=ConsentStore(),
        audit=AuditLogWriter(),
    )
    store = ConsentStore()
    store.grant(
        ConsentGrantRequest(user_id="user-1", service="google_calendar", ttl_hours=4),
    )
    broker = CredentialBroker(
        Settings(google_refresh_token="", vault_mode="memory"),
        consent=store,
        audit=AuditLogWriter(),
        token_exchanger=FakeTokenExchanger(),
    )
    with pytest.raises(CredentialBrokerError, match="GOOGLE_REFRESH_TOKEN"):
        await broker.get_credential("user-1", "google_calendar", "read_events")


async def test_broker_token_exchange_failure_audited() -> None:
    consent = ConsentStore()
    consent.grant(
        ConsentGrantRequest(user_id="user-1", service="google_calendar", ttl_hours=4),
    )
    audit = AuditLogWriter()
    broker = CredentialBroker(
        Settings(
            google_refresh_token="bad-token",
            google_client_id="id",
            google_client_secret="secret",
            vault_mode="memory",
        ),
        consent=consent,
        audit=audit,
        token_exchanger=FakeTokenExchanger(),
    )
    with pytest.raises(CredentialBrokerError):
        await broker.get_credential("user-1", "google_calendar", "read_events")
    assert audit.entries[-1].event_type == "credential_revoked"


async def test_credential_issuance_metric_increments(broker: CredentialBroker) -> None:
    before = CREDENTIAL_ISSUANCE_TOTAL.labels(
        service="google_calendar",
        intent="read_events",
    )._value.get()
    await broker.get_credential("user-1", "google_calendar", "read_events")
    after = CREDENTIAL_ISSUANCE_TOTAL.labels(
        service="google_calendar",
        intent="read_events",
    )._value.get()
    assert after == before + 1


async def test_env_mode_returns_refresh_token_as_mediated_credential(
    consent: ConsentStore,
) -> None:
    broker = CredentialBroker(
        Settings(
            google_refresh_token="refresh-token",
            vault_mode="env",
            credential_ttl_seconds=900,
        ),
        consent=consent,
        audit=AuditLogWriter(),
    )
    credential = await broker.get_credential("user-1", "google_calendar", "read_events")
    assert credential.token_type == "refresh"
    assert credential.access_token == "refresh-token"
    assert credential.expires_at <= datetime.now(UTC) + timedelta(seconds=900)


async def test_supabase_read_credential(consent: ConsentStore) -> None:
    consent.grant(
        ConsentGrantRequest(user_id="user-1", service="postgres_mcp", ttl_hours=4),
    )
    broker = CredentialBroker(
        Settings(
            database_url="postgresql://user:pass@localhost:5432/briefing",
            vault_mode="memory",
        ),
        consent=consent,
        audit=AuditLogWriter(),
        token_exchanger=FakeTokenExchanger(),
    )
    credential = await broker.get_credential("user-1", "supabase", "read_tasks")
    assert "postgresql://" in credential.access_token


async def test_calendar_env_uses_broker(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.mcp import calendar_stdio

    consent = ConsentStore()
    consent.grant(
        ConsentGrantRequest(user_id="user-1", service="google_calendar", ttl_hours=4),
    )
    broker = CredentialBroker(
        Settings(google_refresh_token="refresh-token", vault_mode="env"),
        consent=consent,
        audit=AuditLogWriter(),
    )
    client = calendar_stdio.CalendarMCPStdioClient(
        Settings(google_client_id="cid", google_client_secret="secret"),
        broker=broker,
        user_id="user-1",
    )
    env = await client._build_calendar_env("user-1")
    assert env["GOOGLE_CALENDAR_REFRESH_TOKEN"] == "refresh-token"
    assert env["GOOGLE_CALENDAR_CLIENT_ID"] == "cid"
