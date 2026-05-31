"""PII detection and masking for logs and external LLM calls."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

PII_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    (
        "phone",
        re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "[REDACTED_PHONE]",
    ),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (
        "credit_card",
        re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
        "[REDACTED_CARD]",
    ),
)


class PIIMatch(BaseModel):
    """Detected PII occurrence."""

    model_config = ConfigDict(strict=True, frozen=True)

    kind: str
    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)


class PIIDetector:
    """Regex-based detector for common PII patterns."""

    def detect(self, text: str) -> list[PIIMatch]:
        matches: list[PIIMatch] = []
        for kind, pattern, _placeholder in PII_PATTERNS:
            for match in pattern.finditer(text):
                if kind == "credit_card" and not self._looks_like_card(match.group()):
                    continue
                matches.append(
                    PIIMatch(kind=kind, start=match.start(), end=match.end()),
                )
        return matches

    @staticmethod
    def _looks_like_card(value: str) -> bool:
        digits = re.sub(r"\D", "", value)
        return 13 <= len(digits) <= 19

    def contains_pii(self, text: str) -> bool:
        return bool(self.detect(text))


def mask_pii(text: str) -> str:
    """Replace detected PII with placeholders."""
    masked = text
    for _kind, pattern, placeholder in PII_PATTERNS:
        masked = pattern.sub(placeholder, masked)
    return masked


def mask_mapping_values(data: dict[str, Any]) -> dict[str, Any]:
    """Mask string values in a log/event dictionary."""
    masked: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            masked[key] = mask_pii(value)
        else:
            masked[key] = value
    return masked
