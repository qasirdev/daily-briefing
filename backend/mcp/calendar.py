"""Google Calendar MCP client."""

from __future__ import annotations

import fnmatch
from datetime import date
from typing import Any
from urllib.parse import urlparse

import structlog
from pydantic import BaseModel, ConfigDict, Field

from backend.mcp.client import MCPClient, MCPConsentRequired, MCPError

logger = structlog.get_logger()

GOOGLE_API_ALLOWLIST = ("*.googleapis.com",)


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


def _is_allowed_google_url(url: str) -> bool:
    hostname = urlparse(url).hostname or ""
    return any(fnmatch.fnmatch(hostname, pattern) for pattern in GOOGLE_API_ALLOWLIST)


class CalendarMCPClient(MCPClient):
    """MCP client for Google Calendar read access."""

    def _validate_outbound_urls(self, payload: dict[str, Any]) -> None:
        for key in ("url", "source_url", "api_url"):
            value = payload.get(key)
            if isinstance(value, str) and value and not _is_allowed_google_url(value):
                logger.warning("ssrf_blocked", url=value)
                msg = f"SSRF blocked: disallowed URL {value}"
                raise MCPError(msg)

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
