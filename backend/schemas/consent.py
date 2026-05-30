"""Agentic consent schemas."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

ConsentType = Literal["session", "time_bounded", "recurring"]
ConsentService = Literal["google_calendar", "postgres_mcp"]
AuditAction = Literal[
    "consent_requested",
    "consent_granted",
    "consent_denied",
    "consent_used",
    "consent_expired",
    "consent_revoked",
]

DEFAULT_TTL_HOURS: dict[str, int] = {
    "google_calendar": 4,
    "postgres_mcp": 24,
}


class ConsentRecord(BaseModel):
    """Time-bounded authorization for agent MCP access."""

    model_config = ConfigDict(strict=True)

    id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., min_length=1)
    service: ConsentService
    scope: list[str] = Field(default_factory=list)
    agent_id: str = "calendar"
    consent_type: ConsentType = "time_bounded"
    granted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    times_used: int = Field(default=0, ge=0)
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None

    @property
    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and datetime.now(UTC) > self.expires_at:
            return False
        return True


class ConsentGrantRequest(BaseModel):
    """Request body for granting consent."""

    model_config = ConfigDict(strict=True)

    user_id: str = Field(..., min_length=1)
    service: ConsentService
    scope: list[str] = Field(default_factory=lambda: ["calendar.readonly"])
    agent_id: str = "calendar"
    ttl_hours: int = Field(default=4, ge=0, le=168)
    consent_type: ConsentType | None = None


class ConsentPromptRequest(BaseModel):
    """JIT consent prompt payload returned to the frontend."""

    model_config = ConfigDict(strict=True)

    request_id: str
    service: ConsentService
    scope: list[str]
    suggested_ttl_hours: int = Field(default=4, ge=0)
    agent_requesting: str = "calendar"
    message: str = ""


class ConsentAuditLog(BaseModel):
    """Compliance audit entry for consent operations."""

    model_config = ConfigDict(strict=True)

    id: UUID = Field(default_factory=uuid4)
    user_id: str
    consent_id: UUID | None = None
    action: AuditAction
    service: str = ""
    details: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def calculate_expires_at(
    *,
    service: str,
    consent_type: ConsentType,
    ttl_hours: int,
) -> datetime | None:
    now = datetime.now(UTC)
    if consent_type == "recurring":
        return None
    if consent_type == "session":
        return now + timedelta(minutes=30)
    hours = ttl_hours or DEFAULT_TTL_HOURS.get(service, 4)
    return now + timedelta(hours=hours)
