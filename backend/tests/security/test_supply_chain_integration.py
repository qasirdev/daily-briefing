"""End-to-end supply chain + credential + audit integration (DB-125)."""

from typing import Any

from backend.consent.store import ConsentStore
from backend.schemas.consent import ConsentGrantRequest
from backend.security.audit import AuditLogWriter
from backend.security.bom import validate_bom_against_settings
from backend.security.vault import CredentialBroker
from backend.settings import Settings


class MockExchanger:
    async def exchange_google_refresh_token(
        self,
        *,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> dict[str, Any]:
        del client_id, client_secret, refresh_token
        return {"access_token": "access-123", "expires_in": 900, "token_type": "Bearer"}


async def test_ai_bom_validates_against_live_settings() -> None:
    validate_bom_against_settings(Settings())


async def test_audit_chain_intact_after_credential_flow() -> None:
    consent = ConsentStore()
    consent.grant(
        ConsentGrantRequest(user_id="user-1", service="google_calendar", ttl_hours=4),
    )
    audit = AuditLogWriter()
    broker = CredentialBroker(
        Settings(
            google_refresh_token="refresh",
            google_client_id="id",
            google_client_secret="secret",
            vault_mode="memory",
        ),
        consent=consent,
        audit=audit,
        token_exchanger=MockExchanger(),
    )
    await broker.get_credential("user-1", "google_calendar", "read_events")
    assert audit.verify() is True
    assert any(entry.event_type == "credential_issued" for entry in audit.entries)


async def test_consent_grant_extends_audit_chain() -> None:
    from backend.security.audit import audit_log_writer

    before = len(audit_log_writer.entries)
    store = ConsentStore()
    store.grant(
        ConsentGrantRequest(user_id="consent-audit-user", service="google_calendar", ttl_hours=4),
    )
    new_entries = audit_log_writer.entries[before:]
    assert any(entry.event_type == "consent_granted" for entry in new_entries)


async def test_broker_and_bom_integration_settings() -> None:
    settings = Settings(
        llm_primary_model="openai/gpt-4o-mini",
        embedding_model="openai/text-embedding-3-small",
        google_refresh_token="token",
        google_client_id="test-client-id",
        google_client_secret="test-client-secret",
        vault_mode="memory",
    )
    validate_bom_against_settings(settings)
    consent = ConsentStore()
    consent.grant(
        ConsentGrantRequest(user_id="integration-user", service="google_calendar", ttl_hours=4),
    )
    broker = CredentialBroker(
        settings,
        consent=consent,
        audit=AuditLogWriter(),
        token_exchanger=MockExchanger(),
    )
    credential = await broker.get_credential(
        "integration-user",
        "google_calendar",
        "read_events",
    )
    assert credential.access_token


def test_openssf_minimum_documented_in_bom() -> None:
    from backend.security.bom import load_ai_bom, openssf_scorecard_minimum

    bom = load_ai_bom()
    assert openssf_scorecard_minimum(bom) >= 7.0
    assert bom["metadata"]["supply_chain"]["openssf_scorecard_minimum"] == 7.0
