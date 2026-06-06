"""Google Calendar MCP client over stdio (@franciscpd/calendar-mcp-server)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from typing import Any

import structlog

from backend.mcp.calendar import CalendarEvent
from backend.mcp.client import MCPConsentRequired, MCPError
from backend.mcp.stdio_transport import StdioMCPTransport
from backend.security.ssrf import SSRFValidationError, SSRFValidator
from backend.security.vault import CredentialBroker, credential_broker
from backend.settings import Settings, get_settings

logger = structlog.get_logger()
_ssrf = SSRFValidator()


class CalendarMCPStdioClient(StdioMCPTransport):
    """Stdio MCP client for Google Calendar read access."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        broker: CredentialBroker | None = None,
        user_id: str = "default",
    ) -> None:
        resolved = settings or get_settings()
        self._settings = resolved
        self._broker = broker or credential_broker
        self._user_id = user_id
        super().__init__(
            command="npx",
            args=["-y", "@franciscpd/calendar-mcp-server"],
            server_name="calendar",
            env={},
        )
        self._calendar_id = resolved.calendar_id

    async def _build_calendar_env(self, user_id: str) -> dict[str, str]:
        """Resolve JIT credentials via broker instead of reading refresh token directly."""
        credential = await self._broker.get_credential(
            user_id,
            "google_calendar",
            "read_events",
        )
        env: dict[str, str] = {
            "GOOGLE_CALENDAR_CLIENT_ID": self._settings.google_client_id,
            "GOOGLE_CALENDAR_CLIENT_SECRET": self._settings.google_client_secret,
            "NODE_TLS_REJECT_UNAUTHORIZED": "0",
            "NPM_CONFIG_CACHE": "/tmp/npm-cache",
        }
        if credential.token_type == "refresh":
            env["GOOGLE_CALENDAR_REFRESH_TOKEN"] = credential.access_token
        else:
            env["GOOGLE_CALENDAR_ACCESS_TOKEN"] = credential.access_token
            if self._settings.google_refresh_token:
                env["GOOGLE_CALENDAR_REFRESH_TOKEN"] = self._settings.google_refresh_token
        return env

    async def call_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        self._env = await self._build_calendar_env(self._user_id)
        return await super().call_tool(tool_name, args)

    def _validate_outbound_urls(self, payload: dict[str, Any]) -> None:
        try:
            _ssrf.validate_payload_urls(payload, source="calendar_mcp")
        except SSRFValidationError as exc:
            raise MCPError(str(exc)) from exc

    async def list_calendars(self, *, user_id: str) -> dict[str, Any]:
        self._user_id = user_id
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
        self._user_id = user_id
        resolved_calendar = calendar_id or self._calendar_id
        start = datetime.combine(target_date, time.min, tzinfo=UTC)
        end = datetime.combine(target_date, time.max, tzinfo=UTC)
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
