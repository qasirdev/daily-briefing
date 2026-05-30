"""Prompt injection detection for untrusted external data."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.logging_config import get_security_logger

INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str], float], ...] = (
    ("ignore_previous", re.compile(r"ignore\s+previous", re.IGNORECASE), 0.95),
    ("disregard_training", re.compile(r"disregard\s+training", re.IGNORECASE), 0.95),
    ("debug_mode", re.compile(r"debug\s+mode", re.IGNORECASE), 0.9),
    ("system_brackets", re.compile(r"\[\[SYSTEM\]\]", re.IGNORECASE), 0.98),
    ("im_start", re.compile(r"<\|im_start\|>", re.IGNORECASE), 0.98),
    ("code_system", re.compile(r"```\s*system", re.IGNORECASE | re.DOTALL), 0.92),
)


class InjectionDetectionResult(BaseModel):
    """Outcome of scanning text for prompt injection signatures."""

    model_config = ConfigDict(strict=True, frozen=True)

    is_suspicious: bool
    matched_pattern: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class PromptInjectionDetector:
    """Regex-based detector for known prompt injection signatures."""

    def scan(
        self,
        text: str,
        *,
        trace_id: str,
        source: str = "unknown",
    ) -> InjectionDetectionResult:
        normalized = self._normalize(text)
        if not normalized.strip():
            return InjectionDetectionResult(is_suspicious=False)

        for name, pattern, confidence in INJECTION_PATTERNS:
            if pattern.search(normalized):
                logger = get_security_logger()
                logger.warning(
                    "prompt_injection_detected",
                    trace_id=trace_id,
                    source=source,
                    matched_pattern=name,
                    confidence=confidence,
                )
                return InjectionDetectionResult(
                    is_suspicious=True,
                    matched_pattern=name,
                    confidence=confidence,
                )
        return InjectionDetectionResult(is_suspicious=False)

    def scan_many(
        self,
        texts: dict[str, str],
        *,
        trace_id: str,
    ) -> InjectionDetectionResult:
        for source, text in texts.items():
            result = self.scan(text, trace_id=trace_id, source=source)
            if result.is_suspicious:
                return result
        return InjectionDetectionResult(is_suspicious=False)

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize unicode and collapse whitespace for cross-line matching."""
        normalized = unicodedata.normalize("NFKC", text)
        return re.sub(r"\s+", " ", normalized)


def escalation_reason_from_detection(
    result: InjectionDetectionResult,
) -> Literal["security_violation_detected"] | None:
    if result.is_suspicious:
        return "security_violation_detected"
    return None
