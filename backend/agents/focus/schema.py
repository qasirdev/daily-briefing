"""Focus plan schema validation aligned with prompts/focus/output-schema.md."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

_TIME_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"


class FocusTimeBlock(BaseModel):
    """Single time block in a focus plan."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    start: str = Field(pattern=_TIME_PATTERN)
    end: str = Field(pattern=_TIME_PATTERN)
    activity: str = Field(min_length=1, max_length=200)
    priority: Literal["high", "medium", "low"]
    type: Literal["deep_work", "meeting", "break", "admin"]


class FocusPlan(BaseModel):
    """Validated focus plan payload returned by the Focus agent."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    summary: str = Field(min_length=1, max_length=200)
    time_blocks: list[FocusTimeBlock] = Field(min_length=1, max_length=8)
    top_priorities: list[str] = Field(min_length=3, max_length=5)
    energy_pattern: (
        Literal[
            "morning_peak",
            "afternoon_peak",
            "evening_peak",
            "steady",
        ]
        | None
    ) = None
    notes: str | None = Field(default=None, max_length=300)


MINIMAL_EMPTY_FOCUS_PLAN: dict[str, object] = {
    "summary": "No tasks or calendar events are available today.",
    "time_blocks": [
        {
            "start": "09:00",
            "end": "09:30",
            "activity": "Review goals and plan the day",
            "priority": "medium",
            "type": "admin",
        },
    ],
    "top_priorities": [
        "Review personal goals for today",
        "Check calendar for updates",
        "Plan upcoming work items",
    ],
}


def format_focus_plan_errors(error: ValidationError) -> list[str]:
    """Convert Pydantic validation errors into concise retry hints."""
    messages: list[str] = []
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"])
        messages.append(f"{location}: {item['msg']}")
    return messages


def validate_focus_plan(plan: dict[str, object]) -> list[str]:
    """Return schema validation errors; empty list means the plan is valid."""
    try:
        FocusPlan.model_validate(plan)
    except ValidationError as exc:
        return format_focus_plan_errors(exc)
    return []
