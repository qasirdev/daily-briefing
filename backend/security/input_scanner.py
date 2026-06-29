"""Unified input security scanner — regex, PromptGuard 2, and constitutional layers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.security.constitutional import ConstitutionalClassifier
from backend.security.injection import PromptInjectionDetector
from backend.security.prompt_guard import PromptGuardService, build_prompt_guard_service


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
    prompt_guard_score: float | None = None


class InputSecurityScanner:
    """Scan untrusted text through regex, PromptGuard 2, then constitutional classifiers."""

    def __init__(
        self,
        *,
        regex_detector: PromptInjectionDetector | None = None,
        prompt_guard: PromptGuardService | None = None,
        constitutional: ConstitutionalClassifier | None = None,
    ) -> None:
        self._regex = regex_detector or PromptInjectionDetector()
        self._prompt_guard_override = prompt_guard
        self._prompt_guard: PromptGuardService | None = None
        self._constitutional = constitutional or ConstitutionalClassifier()

    def _get_prompt_guard(self) -> PromptGuardService:
        if self._prompt_guard_override is not None:
            return self._prompt_guard_override
        if self._prompt_guard is None:
            self._prompt_guard = build_prompt_guard_service()
        return self._prompt_guard

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

        pg_result = self._get_prompt_guard().scan(text, trace_id=trace_id, source=source)
        if pg_result.is_blocked:
            return InputScanResult(
                is_blocked=True,
                layer="prompt_guard",
                violation_type=pg_result.reason,
                matched_pattern="prompt_guard",
                confidence=pg_result.score,
                prompt_guard_score=pg_result.score,
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

        return InputScanResult(is_blocked=False, prompt_guard_score=pg_result.score or None)

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
                    prompt_guard_score=result.prompt_guard_score,
                )
        return InputScanResult(is_blocked=False)
