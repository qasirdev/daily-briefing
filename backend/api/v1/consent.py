"""Consent management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from backend.consent.store import consent_store
from backend.schemas.consent import ConsentGrantRequest, ConsentRecord
from backend.settings import get_settings

router = APIRouter(prefix="/api/v1/consent", tags=["consent"])


@router.post("", response_model=ConsentRecord)
async def grant_consent(body: ConsentGrantRequest) -> ConsentRecord:
    """Grant or refresh time-bounded consent for a service."""
    return consent_store.grant(body)


@router.get("", response_model=list[ConsentRecord])
async def list_consents(
    user_id: str = Query(..., min_length=1),
) -> list[ConsentRecord]:
    """List active consents for a user."""
    return consent_store.list_active(user_id)


@router.delete("/{consent_id}", response_model=ConsentRecord)
async def revoke_consent(consent_id: UUID) -> ConsentRecord:
    """Revoke a consent record."""
    record = consent_store.revoke(consent_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent not found")
    return record


@router.get("/oauth/{service}")
async def oauth_redirect(service: str) -> dict[str, str]:
    """Return OAuth authorize URL for a service (Google Calendar)."""
    settings = get_settings()
    if service == "google_calendar":
        oauth_url = settings.resolved_google_oauth_authorize_url
        if oauth_url:
            return {"oauth_url": oauth_url, "service": service}
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"OAuth not configured for service: {service}",
    )
