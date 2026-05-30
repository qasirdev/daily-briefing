"""Tests for preference feedback."""

import pytest

from backend.preferences.store import PreferenceStore, extract_preference
from backend.schemas.preferences import PreferenceFeedbackRequest
from backend.tests.http_client import api_client


def test_no_preference_when_unchanged() -> None:
    feedback = PreferenceFeedbackRequest(
        user_id="user-1",
        briefing_id="brief-1",
        original_content="Same text",
        edited_content="Same text",
    )
    assert extract_preference(feedback) is None


def test_extract_morning_preference() -> None:
    feedback = PreferenceFeedbackRequest(
        user_id="user-1",
        briefing_id="brief-1",
        original_content="Plan for the day",
        edited_content="Prefer morning deep work blocks",
    )
    pref = extract_preference(feedback)
    assert pref is not None
    assert "morning" in pref.preference_text


@pytest.mark.asyncio
async def test_feedback_endpoint() -> None:
    async with api_client() as client:
        response = await client.post(
            "/api/v1/preferences/feedback",
            json={
                "user_id": "user-1",
                "briefing_id": "brief-1",
                "original_content": "Plan",
                "edited_content": "Keep it shorter please",
            },
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["extracted"] is True


def test_conflicting_preferences_keep_highest_confidence() -> None:
    store = PreferenceStore()
    first = store.add(
        extract_preference(
            PreferenceFeedbackRequest(
                user_id="user-1",
                briefing_id="b1",
                original_content="x",
                edited_content="Prefer morning deep work",
            ),
        )  # type: ignore[arg-type]
    )
    second = store.add(
        extract_preference(
            PreferenceFeedbackRequest(
                user_id="user-1",
                briefing_id="b2",
                original_content="x",
                edited_content="Prefer morning focus time",
            ),
        )  # type: ignore[arg-type]
    )
    assert first is not None and second is not None
    assert first.id == second.id
