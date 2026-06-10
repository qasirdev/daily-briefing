"""Prompt injection detection for untrusted external data."""

from __future__ import annotations

import base64
import binascii
import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from rapidfuzz import fuzz

from backend.logging_config import get_security_logger
from backend.security.injection_patterns import INJECTION_PATTERNS

# OWASP-recommended fuzzy phrases for obfuscation-resistant matching (partial_ratio ≥ threshold).
FUZZY_CANONICAL_PHRASES: tuple[tuple[str, str, float], ...] = (
    ("ignore_previous", "ignore previous instructions", 0.88),
    ("disregard_previous", "disregard all previous instructions", 0.88),
    ("disregard_training", "disregard training", 0.88),
)

_FUZZY_THRESHOLD = 88
_ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200d\ufeff\u2060]")
_HEX_ESCAPE_RE = re.compile(r"\\x([0-9a-fA-F]{2})")
_BASE64_RE = re.compile(r"^[A-Za-z0-9+/=\s]+$")


class InjectionDetectionResult(BaseModel):
    """Outcome of scanning text for prompt injection signatures."""

    model_config = ConfigDict(strict=True, frozen=True)

    is_suspicious: bool
    matched_pattern: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class PromptInjectionDetector:
    """Regex and fuzzy-match detector for known prompt injection signatures."""

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
                return self._blocked(name, confidence, trace_id=trace_id, source=source)

        fuzzy = self._fuzzy_match(normalized)
        if fuzzy is not None:
            name, confidence = fuzzy
            return self._blocked(name, confidence, trace_id=trace_id, source=source)

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
        """Normalize unicode, decode obfuscation, and collapse whitespace."""
        decoded = PromptInjectionDetector._decode_hex_escapes(text)
        stripped = _ZERO_WIDTH_RE.sub("", decoded)
        normalized = unicodedata.normalize("NFKC", stripped)
        with_b64 = PromptInjectionDetector._append_base64_decoded(normalized)
        return re.sub(r"\s+", " ", with_b64)

    @staticmethod
    def _decode_hex_escapes(text: str) -> str:
        def _replace(match: re.Match[str]) -> str:
            return chr(int(match.group(1), 16))

        return _HEX_ESCAPE_RE.sub(_replace, text)

    @staticmethod
    def _append_base64_decoded(text: str) -> str:
        candidate = text.strip()
        if not candidate or not _BASE64_RE.match(candidate):
            return text
        compact = re.sub(r"\s+", "", candidate)
        if len(compact) < 8 or len(compact) % 4 != 0:
            return text
        try:
            decoded = base64.b64decode(compact, validate=True).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            return text
        return f"{text} {decoded}"

    @staticmethod
    def _fuzzy_match(text: str) -> tuple[str, float] | None:
        lowered = text.lower()
        best: tuple[str, float, float] | None = None
        for name, phrase, confidence in FUZZY_CANONICAL_PHRASES:
            score = fuzz.partial_ratio(phrase, lowered)
            if score >= _FUZZY_THRESHOLD and (best is None or score > best[2]):
                best = (name, confidence, score)
        if best is None:
            return None
        return best[0], best[1]

    @staticmethod
    def _blocked(
        name: str,
        confidence: float,
        *,
        trace_id: str,
        source: str,
    ) -> InjectionDetectionResult:
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


def escalation_reason_from_detection(
    result: InjectionDetectionResult,
) -> Literal["security_violation_detected"] | None:
    if result.is_suspicious:
        return "security_violation_detected"
    return None
