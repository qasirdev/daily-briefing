"""Tests for consent store and API."""

from uuid import uuid4

import pytest

from backend.consent.store import ConsentStore
from backend.schemas.consent import ConsentGrantRequest
from backend.tests.http_client import api_client


@pytest.fixture
def store() -> ConsentStore:
    return ConsentStore()


def test_grant_creates_record(store: ConsentStore) -> None:
    record = store.grant(
        ConsentGrantRequest(
            user_id="user-1",
            service="google_calendar",
            scope=["calendar.readonly"],
            ttl_hours=4,
        ),
    )
    assert record.is_active
    assert record.service == "google_calendar"


def test_grant_updates_existing_service(store: ConsentStore) -> None:
    first = store.grant(
        ConsentGrantRequest(
            user_id="user-1",
            service="google_calendar",
            scope=["calendar.readonly"],
            ttl_hours=1,
        ),
    )
    second = store.grant(
        ConsentGrantRequest(
            user_id="user-1",
            service="google_calendar",
            scope=["calendar.readonly", "calendar.events"],
            ttl_hours=4,
        ),
    )
    assert first.id == second.id
    assert len(second.scope) == 2


def test_list_active_excludes_revoked(store: ConsentStore) -> None:
    record = store.grant(
        ConsentGrantRequest(
            user_id="user-1",
            service="google_calendar",
            scope=["calendar.readonly"],
            ttl_hours=4,
        ),
    )
    store.revoke(record.id)
    assert store.list_active("user-1") == []


@pytest.mark.asyncio
async def test_consent_api_grant_and_list() -> None:
    async with api_client() as client:
        grant = await client.post(
            "/api/v1/consent",
            json={
                "user_id": "user-1",
                "service": "google_calendar",
                "scope": ["calendar.readonly"],
                "ttl_hours": 4,
            },
        )
        assert grant.status_code == 200
        listed = await client.get("/api/v1/consent", params={"user_id": "user-1"})
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


@pytest.mark.asyncio
async def test_consent_api_revoke_not_found() -> None:
    async with api_client() as client:
        response = await client.delete(f"/api/v1/consent/{uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_consent_oauth_google_calendar(monkeypatch: pytest.MonkeyPatch) -> None:
    from backend.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8088")
    monkeypatch.delenv("GOOGLE_OAUTH_AUTHORIZE_URL", raising=False)
    get_settings.cache_clear()

    async with api_client() as client:
        response = await client.get("/api/v1/consent/oauth/google_calendar")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "google_calendar"
    assert "client_id=test-client-id" in payload["oauth_url"]
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8088" in payload["oauth_url"]
    get_settings.cache_clear()
