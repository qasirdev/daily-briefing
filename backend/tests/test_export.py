"""Tests for GDPR export endpoint."""

from fastapi.testclient import TestClient

from backend.consent.store import consent_store
from backend.main import create_app
from backend.schemas.consent import ConsentGrantRequest
from backend.settings import Settings


def test_export_json_includes_sections() -> None:
    consent_store.grant(
        ConsentGrantRequest(
            user_id="user-1",
            service="google_calendar",
            scope=["calendar.readonly"],
            ttl_hours=4,
        ),
    )
    client = TestClient(create_app(Settings()))
    response = client.get("/api/v1/export", params={"user_id": "user-1", "format": "json"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == "user-1"
    assert "consent_records" in payload
    assert "preferences" in payload


def test_export_empty_user() -> None:
    client = TestClient(create_app(Settings()))
    response = client.get("/api/v1/export", params={"user_id": "empty-user", "format": "json"})
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("message") == "No stored data for user"
