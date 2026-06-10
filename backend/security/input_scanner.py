"""Unified input security scanner — regex + constitutional layers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.security.constitutional_classifier import ConstitutionalClassifier
from backend.security.injection import PromptInjectionDetector


class InputScanResult(BaseModel):
    """Combined outcome of multi-layer input scanning."""

    model_config = ConfigDict(strict=True, frozen=True)

    is_blocked: bool
    layer: str | None = None
    violation_type: str | None = None
    matched_pattern: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    constitutional_rule: str | None = None
    blocked_source: str | None = None


class InputSecurityScanner:
    """Scan untrusted text through regex then constitutional classifiers."""

    def __init__(
        self,
        *,
        regex_detector: PromptInjectionDetector | None = None,
        constitutional: ConstitutionalClassifier | None = None,
    ) -> None:
        self._regex = regex_detector or PromptInjectionDetector()
        self._constitutional = constitutional or ConstitutionalClassifier()

    def scan(
        self,
        text: str,
        *,
        trace_id: str,
        source: str = "unknown",
    ) -> InputScanResult:
        regex_result = self._regex.scan(text, trace_id=trace_id, source=source)
        if regex_result.is_suspicious:
            return InputScanResult(
                is_blocked=True,
                layer="regex",
                violation_type=regex_result.matched_pattern,
                matched_pattern=regex_result.matched_pattern,
                confidence=regex_result.confidence,
            )

        constitutional_result = self._constitutional.classify(
            text,
            trace_id=trace_id,
            source=source,
        )
        if constitutional_result.is_violation:
            return InputScanResult(
                is_blocked=True,
                layer="constitutional",
                violation_type=constitutional_result.violated_rule,
                matched_pattern=constitutional_result.matched_pattern,
                confidence=constitutional_result.confidence,
                constitutional_rule=constitutional_result.violated_rule,
            )

        return InputScanResult(is_blocked=False)

    def scan_many(
        self,
        texts: dict[str, str],
        *,
        trace_id: str,
    ) -> InputScanResult:
        for source, text in texts.items():
            result = self.scan(text, trace_id=trace_id, source=source)
            if result.is_blocked:
                return InputScanResult(
                    is_blocked=True,
                    layer=result.layer,
                    violation_type=result.violation_type,
                    matched_pattern=result.matched_pattern,
                    confidence=result.confidence,
                    constitutional_rule=result.constitutional_rule,
                    blocked_source=source,
                )
        return InputScanResult(is_blocked=False)
