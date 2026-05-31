"""Google Calendar MCP client."""

from __future__ import annotations

from datetime import date
from typing import Any

import structlog
from pydantic import BaseModel, ConfigDict, Field

from backend.mcp.client import MCPClient, MCPConsentRequired, MCPError
from backend.security.ssrf import SSRFValidationError, SSRFValidator

logger = structlog.get_logger()
_ssrf = SSRFValidator()


class CalendarEvent(BaseModel):
    """Structured calendar event from MCP."""

    model_config = ConfigDict(strict=True, frozen=True)

    id: str
    summary: str
    start: str
    end: str
    description: str = ""
    attendees: list[str] = Field(default_factory=list)
    location: str = ""


class CalendarMCPClient(MCPClient):
    """MCP client for Google Calendar read access."""

    def _validate_outbound_urls(self, payload: dict[str, Any]) -> None:
        try:
            _ssrf.validate_payload_urls(payload, source="calendar_mcp")
        except SSRFValidationError as exc:
            raise MCPError(str(exc)) from exc

    async def list_calendars(self, *, user_id: str) -> dict[str, Any]:
        payload = await self.call_tool("list_calendars", {"user_id": user_id})
        self._validate_outbound_urls(payload)
        return payload

    async def get_events(
        self,
        *,
        user_id: str,
        target_date: date,
        calendar_id: str = "primary",
    ) -> list[CalendarEvent]:
        try:
            payload = await self.call_tool(
                "get_events",
                {
                    "user_id": user_id,
                    "calendar_id": calendar_id,
                    "date": target_date.isoformat(),
                },
            )
        except MCPConsentRequired:
            raise
        except MCPError:
            if calendar_id != "primary":
                return []
            raise

        self._validate_outbound_urls(payload)
        events: list[CalendarEvent] = []
        for raw in payload.get("events", []):
            if not isinstance(raw, dict):
                continue
            start = str(raw.get("start", ""))
            end = str(raw.get("end", "")) or start
            events.append(
                CalendarEvent(
                    id=str(raw.get("id", "")),
                    summary=str(raw.get("summary", "Untitled")),
                    start=start,
                    end=end if end else start,
                    description=str(raw.get("description", "")),
                    attendees=[str(a) for a in raw.get("attendees", []) if a],
                    location=str(raw.get("location", "")),
                ),
            )
        return events
