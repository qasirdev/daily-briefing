"""E2E consent grant, use, and revoke cycle."""

from uuid import uuid4

import pytest

from backend.consent import store as consent_module
from backend.consent.store import ConsentStore
from backend.tests.http_client import api_client


@pytest.mark.asyncio
async def test_consent_grant_list_revoke_cycle(monkeypatch: pytest.MonkeyPatch) -> None:
    store = ConsentStore()
    monkeypatch.setattr(consent_module, "consent_store", store)
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
        consent_id = grant.json()["id"]

        listed = await client.get("/api/v1/consent", params={"user_id": "user-1"})
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        revoked = await client.delete(f"/api/v1/consent/{consent_id}")
        assert revoked.status_code == 200

        empty = await client.get("/api/v1/consent", params={"user_id": "user-1"})
        assert empty.json() == []


@pytest.mark.asyncio
async def test_consent_revoke_missing_returns_404() -> None:
    async with api_client() as client:
        response = await client.delete(f"/api/v1/consent/{uuid4()}")
    assert response.status_code == 404
