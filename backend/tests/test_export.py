"""Tests for GDPR export endpoint."""

import pytest

from backend.consent.store import consent_store
from backend.schemas.consent import ConsentGrantRequest
from backend.tests.http_client import api_client


@pytest.mark.asyncio
async def test_export_json_includes_sections() -> None:
    consent_store.grant(
        ConsentGrantRequest(
            user_id="user-1",
            service="google_calendar",
            scope=["calendar.readonly"],
            ttl_hours=4,
        ),
    )
    async with api_client() as client:
        response = await client.get("/api/v1/export", params={"user_id": "user-1", "format": "json"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "user-1"
    assert "consent_records" in payload
    assert "preferences" in payload


@pytest.mark.asyncio
async def test_export_empty_user() -> None:
    async with api_client() as client:
        response = await client.get(
            "/api/v1/export",
            params={"user_id": "empty-user", "format": "json"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("message") == "No stored data for user"
