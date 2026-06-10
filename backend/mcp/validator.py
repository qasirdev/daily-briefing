"""MCP response validation layer for tool poisoning defense (Gap #117)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, cast

import nh3
from pydantic import BaseModel, Field, ValidationInfo, field_validator

from backend.security.spotlighting import spotlight_external_content

INJECTION_SIGNATURES = re.compile(
    r"(ignore\s+(all\s+)?previous|<<<\s*system|```\s*system|\[\[SYSTEM\]\])",
    re.IGNORECASE,
)

ALLOWED_URL_PREFIXES = (
    "https://www.googleapis.com/calendar/",
    "https://accounts.google.com/o/oauth2/",
)


class ValidationResult(BaseModel):
    """Outcome of MCP response validation."""

    valid: bool
    sanitized_response: dict[str, Any] | None = None
    quarantine: bool = False
    issues: list[str] = Field(default_factory=list)


class CalendarEventSchema(BaseModel):
    """Schema validation for calendar MCP event payloads."""

    title: str = Field(..., max_length=200)
    start: str
    end: str
    attendees: list[str] = Field(default_factory=list)

    @field_validator("end")
    @classmethod
    def end_after_start(cls, end: str, info: ValidationInfo) -> str:
        start = info.data.get("start")
        if not start:
            return end
        try:
            start_dt = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        except ValueError:
            return end
        if end_dt <= start_dt:
            msg = "End must be after start"
            raise ValueError(msg)
        return end


class MCPResponseValidator:
    """Three-layer defense: schema, sanitization, anomaly detection."""

    def __init__(self, *, baseline_field_count: int = 5, baseline_size_bytes: int = 2048) -> None:
        self._baseline_field_count = baseline_field_count
        self._baseline_size_bytes = baseline_size_bytes

    def validate(self, tool: str, response: dict[str, Any]) -> ValidationResult:
        issues: list[str] = []
        injection_hits = self._detect_injection(response)
        sanitized = self._sanitize_response(response)

        if tool == "calendar.read_events":
            events = sanitized.get("events", [])
            if isinstance(events, list):
                for index, event in enumerate(events):
                    if not isinstance(event, dict):
                        issues.append(f"event[{index}] is not an object")
                        continue
                    try:
                        CalendarEventSchema(
                            title=str(event.get("summary") or event.get("title") or ""),
                            start=str(event.get("start", "")),
                            end=str(event.get("end", "")),
                            attendees=[
                                str(item) for item in event.get("attendees", []) if item is not None
                            ],
                        )
                    except ValueError as exc:
                        issues.append(f"event[{index}]: {exc}")

        if tool == "tasks.list":
            rows = sanitized.get("rows", [])
            if isinstance(rows, list):
                for index, row in enumerate(rows):
                    if not isinstance(row, dict):
                        issues.append(f"row[{index}] is not an object")
                        continue
                    title = row.get("title")
                    if title is not None and len(str(title)) > 500:
                        issues.append(f"row[{index}]: title exceeds 500 characters")

        issues.extend(injection_hits)

        anomaly = self._detect_anomaly(sanitized)
        if anomaly:
            issues.append(anomaly)

        if issues:
            return ValidationResult(
                valid=False,
                sanitized_response=sanitized,
                quarantine=bool(injection_hits or anomaly),
                issues=issues,
            )
        return ValidationResult(valid=True, sanitized_response=sanitized)

    def _sanitize_response(self, response: dict[str, Any]) -> dict[str, Any]:
        def clean_value(value: Any) -> Any:
            if isinstance(value, str):
                cleaned = nh3.clean(value, tags=set())
                if INJECTION_SIGNATURES.search(cleaned):
                    return spotlight_external_content(cleaned)
                return cleaned
            if isinstance(value, dict):
                return {key: clean_value(item) for key, item in value.items()}
            if isinstance(value, list):
                return [clean_value(item) for item in value]
            return value

        return cast(dict[str, Any], clean_value(response))

    def _detect_injection(self, payload: dict[str, Any]) -> list[str]:
        findings: list[str] = []

        def walk(value: Any, path: str) -> None:
            if isinstance(value, str) and INJECTION_SIGNATURES.search(value):
                findings.append(f"injection_signature in field '{path}'")
            elif isinstance(value, dict):
                for key, item in value.items():
                    walk(item, f"{path}.{key}" if path else str(key))
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    walk(item, f"{path}[{index}]")

        walk(payload, "")
        return findings

    def _detect_anomaly(self, payload: dict[str, Any]) -> str | None:
        serialized = str(payload)
        size = len(serialized.encode("utf-8"))
        if size > self._baseline_size_bytes * 10:
            return f"response size anomaly: {size} bytes"
        field_count = len(serialized.split(","))
        if field_count > self._baseline_field_count * 10:
            return f"field count anomaly: {field_count}"
        return None
