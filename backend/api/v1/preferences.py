"""User preference feedback endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from backend.preferences.store import extract_preference, preference_store
from backend.schemas.preferences import (
    PreferenceFeedbackRequest,
    PreferenceFeedbackResponse,
    UserPreference,
)

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])


@router.post("/feedback", response_model=PreferenceFeedbackResponse)
async def submit_feedback(body: PreferenceFeedbackRequest) -> PreferenceFeedbackResponse:
    """Extract and store a preference from briefing edits."""
    extracted = extract_preference(body)
    if extracted is None:
        return PreferenceFeedbackResponse(
            extracted=False,
            message="No preference detected from edits",
        )
    stored = preference_store.add(extracted)
    return PreferenceFeedbackResponse(
        extracted=True,
        preference=stored,
        message="Preference saved for future briefings",
    )


@router.get("", response_model=list[UserPreference])
async def list_preferences(
    user_id: str = Query(..., min_length=1),
) -> list[UserPreference]:
    return preference_store.list_for_user(user_id)


@router.delete("/{preference_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preference(preference_id: UUID) -> None:
    if not preference_store.delete(preference_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")
