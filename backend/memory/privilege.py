"""Privilege lifecycle helpers for episodic memory (Gap #119)."""

from __future__ import annotations

import re

_PRIVILEGE_REDACT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:password|credential|api[_-]?key|secret[_-]?key|access[_-]?token|bearer)"
        r"(?:\s+\w+)?\s*[:=]\s*\S+",
        re.IGNORECASE,
    ),
    re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b", re.IGNORECASE),
    re.compile(
        r"\b(?:admin|root|sudo)\s+(?:access|rights|privileges?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:has|have|holds?|retains?)\s+(?:admin|root|sudo)\s+(?:access|rights)\b",
        re.IGNORECASE,
    ),
)

_REDACTED = "[REDACTED]"


def _is_only_redactions(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    return bool(re.fullmatch(r"(?:\[REDACTED\]\s*)+", stripped))


def sanitize_lesson_content(content: str) -> str:
    """Redact credential and active-privilege patterns from episodic lessons."""
    sanitized = content.strip()
    if not sanitized:
        return ""

    for pattern in _PRIVILEGE_REDACT_PATTERNS:
        sanitized = pattern.sub(_REDACTED, sanitized)

    sanitized = sanitized.strip()
    if _is_only_redactions(sanitized):
        return ""
    return sanitized
