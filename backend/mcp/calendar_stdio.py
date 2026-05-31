"""Google Calendar MCP client over stdio (@franciscpd/calendar-mcp-server)."""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any

import structlog

from backend.mcp.calendar import CalendarEvent
from backend.mcp.client import MCPConsentRequired, MCPError
from backend.mcp.stdio_transport import StdioMCPTransport
from backend.security.ssrf import SSRFValidationError, SSRFValidator
from backend.settings import Settings, get_settings

logger = structlog.get_logger()
_ssrf = SSRFValidator()


class CalendarMCPStdioClient(StdioMCPTransport):
    """Stdio MCP client for Google Calendar read access."""

    def __init__(self, settings: Settings | None = None) -> None:
        resolved = settings or get_settings()
        super().__init__(
            command="npx",
            args=["-y", "@franciscpd/calendar-mcp-server"],
            server_name="calendar",
            env={
                "GOOGLE_CALENDAR_CLIENT_ID": resolved.google_client_id,
                "GOOGLE_CALENDAR_CLIENT_SECRET": resolved.google_client_secret,
                "GOOGLE_CALENDAR_REFRESH_TOKEN": resolved.google_refresh_token,
                "NODE_TLS_REJECT_UNAUTHORIZED": "0",
                "NPM_CONFIG_CACHE": "/tmp/npm-cache",
            },
        )
        self._calendar_id = resolved.calendar_id

    def _validate_outbound_urls(self, payload: dict[str, Any]) -> None:
        try:
            _ssrf.validate_payload_urls(payload, source="calendar_mcp")
        except SSRFValidationError as exc:
            raise MCPError(str(exc)) from exc

    async def list_calendars(self, *, user_id: str) -> dict[str, Any]:
        payload = await self.call_tool("calendar_list_calendars", {})
        self._validate_outbound_urls(payload if isinstance(payload, dict) else {})
        calendars = payload.get("calendars", payload.get("items", []))
        return {"calendars": calendars, "user_id": user_id}

    async def get_events(
        self,
        *,
        user_id: str,
        target_date: date,
        calendar_id: str = "primary",
    ) -> list[CalendarEvent]:
        resolved_calendar = calendar_id or self._calendar_id
        start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)
        try:
            payload = await self.call_tool(
                "calendar_list_events",
                {
                    "calendar_id": resolved_calendar,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                },
            )
        except MCPConsentRequired:
            raise
        except MCPError:
            if resolved_calendar != "primary":
                return []
            raise

        self._validate_outbound_urls(payload if isinstance(payload, dict) else {})
        raw_events = payload.get("events", payload.get("items", []))
        events: list[CalendarEvent] = []
        if not isinstance(raw_events, list):
            return events

        for raw in raw_events:
            if not isinstance(raw, dict):
                continue
            start_value = _event_time(raw.get("start"))
            end_value = _event_time(raw.get("end")) or start_value
            attendees_raw = raw.get("attendees", [])
            attendees = (
                [str(a.get("email", a)) for a in attendees_raw if isinstance(a, dict)]
                if isinstance(attendees_raw, list)
                else []
            )
            events.append(
                CalendarEvent(
                    id=str(raw.get("id", "")),
                    summary=str(raw.get("summary", raw.get("title", "Untitled"))),
                    start=start_value,
                    end=end_value or start_value,
                    description=str(raw.get("description", "")),
                    attendees=attendees,
                    location=str(raw.get("location", "")),
                ),
            )
        return events


def _event_time(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if "dateTime" in value:
            return str(value["dateTime"])
        if "date" in value:
            return str(value["date"])
    return ""
