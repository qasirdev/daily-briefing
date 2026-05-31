"""British date/time formatting for briefing output."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")


def format_event_time_london(value: Any) -> str:
    """Format a datetime as ``DD-MM-YYYY at HH:MM`` or ``DD-MM-YYYY`` (Europe/London)."""
    text = value.strip() if isinstance(value, str) else str(value).strip()
    if not text:
        return ""
    if len(text) >= 10 and text[2:3] == "-" and text[5:6] == "-":
        return text
    if "T" not in text:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%d-%m-%Y")
        except ValueError:
            return text[:10] if len(text) >= 10 else text
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=LONDON)
    return parsed.astimezone(LONDON).strftime("%d-%m-%Y at %H:%M")


def format_time_range(start: Any, end: Any) -> str:
    """Format a start/end pair for display, compacting same-day ranges."""
    start_text = format_event_time_london(start)
    end_text = format_event_time_london(end)
    if (
        start_text
        and end_text
        and " at " in start_text
        and " at " in end_text
        and start_text[:10] == end_text[:10]
    ):
        return f"{start_text} – {end_text.split(' at ', 1)[1]}"
    if start_text and end_text:
        return f"{start_text} – {end_text}"
    return start_text or end_text or "Scheduled"
