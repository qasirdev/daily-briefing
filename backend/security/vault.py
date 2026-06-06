"""JIT credential broker for MCP integrations (Gap #19)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, Protocol

import httpx
import structlog

from backend.consent.store import ConsentStore, consent_store
from backend.observability.metrics import record_credential_issuance
from backend.security.audit import AuditLogWriter, audit_log_writer
from backend.settings import Settings, get_settings

logger = structlog.get_logger()

CredentialService = Literal["google_calendar", "supabase"]
CredentialIntent = Literal["read_events", "read_tasks", "update_tasks"]

CONSENT_SERVICE_MAP: dict[CredentialService, str] = {
    "google_calendar": "google_calendar",
    "supabase": "postgres_mcp",
}

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
OAUTH_SETUP_GUIDE = "docs/guidence/google-calandar-setup.md"


class CredentialDeniedError(Exception):
    """Raised when consent or authorization blocks credential issuance."""


class CredentialBrokerError(Exception):
    """Raised when credential exchange fails."""


@dataclass(frozen=True)
class Credential:
    """Short-lived credential issued on demand."""

    access_token: str
    token_type: str
    expires_at: datetime
    service: CredentialService
    intent: CredentialIntent


class TokenExchanger(Protocol):
    """Protocol for OAuth token exchange (mockable in tests)."""

    async def exchange_google_refresh_token(
        self,
        *,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> dict[str, Any]:
        """Exchange a Google refresh token for an access token response."""


class GoogleTokenExchanger:
    """Default Google OAuth2 refresh-token exchange."""

    async def exchange_google_refresh_token(
        self,
        *,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                },
            )
        if response.status_code >= 400:
            msg = f"Google token exchange failed: HTTP {response.status_code}"
            raise CredentialBrokerError(msg)
        payload = response.json()
        if not isinstance(payload, dict) or "access_token" not in payload:
            msg = "Google token exchange returned invalid payload"
            raise CredentialBrokerError(msg)
        return payload


@dataclass
class _CacheEntry:
    credential: Credential
    audit_logged: bool


class CredentialBroker:
    """Issue short-lived credentials with consent checks and audit trail."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        consent: ConsentStore | None = None,
        audit: AuditLogWriter | None = None,
        token_exchanger: TokenExchanger | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._consent = consent or consent_store
        self._audit = audit or audit_log_writer
        self._token_exchanger = token_exchanger or GoogleTokenExchanger()
        self._cache: dict[str, _CacheEntry] = {}

    def _cache_key(self, user_id: str, service: CredentialService, intent: CredentialIntent) -> str:
        return f"{user_id}:{service}:{intent}"

    async def get_credential(
        self,
        user_id: str,
        service: CredentialService,
        intent: CredentialIntent,
        ttl_seconds: int | None = None,
    ) -> Credential:
        """Issue a short-lived credential on demand."""
        if user_id.strip() != user_id or not user_id.strip():
            msg = "user_id is required for credential issuance"
            raise CredentialDeniedError(msg)

        ttl = ttl_seconds if ttl_seconds is not None else self._settings.credential_ttl_seconds
        if ttl <= 0:
            msg = "ttl_seconds must be positive"
            raise ValueError(msg)

        consent_service = CONSENT_SERVICE_MAP[service]
        if not self._consent.has_valid_consent(user_id, consent_service):
            msg = f"Consent required for {service} before credential issuance"
            raise CredentialDeniedError(msg)

        cache_key = self._cache_key(user_id, service, intent)
        cached = self._cache.get(cache_key)
        now = datetime.now(UTC)
        if cached is not None and cached.credential.expires_at > now:
            return cached.credential

        try:
            credential = await self._issue_credential(
                user_id=user_id,
                service=service,
                intent=intent,
                ttl_seconds=ttl,
            )
        except CredentialBrokerError:
            self._audit.append(
                event_type="credential_revoked",
                actor_id=user_id,
                resource=service,
                payload={"intent": intent, "reason": "token_exchange_failed"},
            )
            raise

        self._cache[cache_key] = _CacheEntry(credential=credential, audit_logged=True)
        self._audit.append(
            event_type="credential_issued",
            actor_id=user_id,
            resource=service,
            payload={"intent": intent, "expires_at": credential.expires_at.isoformat()},
        )
        record_credential_issuance(service=service, intent=intent)
        self._consent.record_usage(user_id, consent_service)
        return credential

    async def _issue_credential(
        self,
        *,
        user_id: str,
        service: CredentialService,
        intent: CredentialIntent,
        ttl_seconds: int,
    ) -> Credential:
        del user_id  # reserved for per-user token stores in production vault
        if service == "google_calendar":
            return await self._issue_google_calendar(intent=intent, ttl_seconds=ttl_seconds)
        if service == "supabase":
            return self._issue_supabase_read(ttl_seconds=ttl_seconds)
        msg = f"Unsupported credential service: {service}"
        raise CredentialBrokerError(msg)

    async def _issue_google_calendar(
        self,
        *,
        intent: CredentialIntent,
        ttl_seconds: int,
    ) -> Credential:
        refresh_token = self._settings.google_refresh_token.strip()
        if not refresh_token:
            msg = (
                f"GOOGLE_REFRESH_TOKEN is not configured. Complete OAuth setup: {OAUTH_SETUP_GUIDE}"
            )
            raise CredentialBrokerError(msg)

        if self._settings.vault_mode == "env":
            expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
            return Credential(
                access_token=refresh_token,
                token_type="refresh",
                expires_at=expires_at,
                service="google_calendar",
                intent=intent,
            )

        if not self._settings.google_client_id or not self._settings.google_client_secret:
            msg = "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are required for token exchange"
            raise CredentialBrokerError(msg)

        payload = await self._token_exchanger.exchange_google_refresh_token(
            client_id=self._settings.google_client_id,
            client_secret=self._settings.google_client_secret,
            refresh_token=refresh_token,
        )
        access_token = str(payload["access_token"])
        expires_in = int(payload.get("expires_in", ttl_seconds))
        effective_ttl = min(ttl_seconds, expires_in)
        expires_at = datetime.now(UTC) + timedelta(seconds=effective_ttl)
        return Credential(
            access_token=access_token,
            token_type=str(payload.get("token_type", "Bearer")),
            expires_at=expires_at,
            service="google_calendar",
            intent=intent,
        )

    def _issue_supabase_read(self, *, ttl_seconds: int) -> Credential:
        database_url = self._settings.resolved_mcp_postgres_url
        if not database_url:
            msg = "DATABASE_URL / MCP_POSTGRES_URL is not configured"
            raise CredentialBrokerError(msg)
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        return Credential(
            access_token=database_url,
            token_type="connection_string",
            expires_at=expires_at,
            service="supabase",
            intent="read_tasks",
        )


credential_broker = CredentialBroker()
