"""Constitutional classifier for jailbreak detection (Gap #126)."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from backend.logging_config import get_security_logger

RULES_PATH = Path(__file__).resolve().parent / "rules.yaml"


class ConstitutionalRule(BaseModel):
    """Single constitutional rule loaded from rules.yaml."""

    model_config = ConfigDict(strict=True, frozen=True)

    id: str
    description: str
    patterns: list[str]
    severity: str = "high"
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class ConstitutionalResult(BaseModel):
    """Outcome of constitutional classification."""

    model_config = ConfigDict(strict=True, frozen=True)

    is_violation: bool
    violated_rule: str | None = None
    severity: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_pattern: str | None = None


class ConfigurationError(RuntimeError):
    """Raised when constitutional rules cannot be loaded."""


@lru_cache(maxsize=1)
def load_constitutional_rules() -> tuple[ConstitutionalRule, ...]:
    """Load and cache constitutional rules from rules.yaml."""
    if not RULES_PATH.is_file():
        raise ConfigurationError(f"Constitutional rules missing: {RULES_PATH}")

    raw = yaml.safe_load(RULES_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "rules" not in raw:
        raise ConfigurationError("rules.yaml must contain a top-level 'rules' list")

    rules_raw = raw["rules"]
    if not isinstance(rules_raw, list) or not rules_raw:
        raise ConfigurationError("rules.yaml 'rules' list must be non-empty")

    rules: list[ConstitutionalRule] = []
    seen_ids: set[str] = set()
    for item in rules_raw:
        if not isinstance(item, dict):
            continue
        rule = ConstitutionalRule.model_validate(item)
        if rule.id in seen_ids:
            raise ConfigurationError(f"Duplicate constitutional rule id: {rule.id}")
        seen_ids.add(rule.id)
        rules.append(rule)

    return tuple(rules)


class ConstitutionalClassifier:
    """Rule-based constitutional classifier for jailbreak and policy violations."""

    def __init__(self, rules: tuple[ConstitutionalRule, ...] | None = None) -> None:
        self._rules = rules if rules is not None else load_constitutional_rules()
        self._compiled: list[tuple[ConstitutionalRule, re.Pattern[str], str]] = []
        for rule in self._rules:
            for pattern in rule.patterns:
                self._compiled.append((rule, re.compile(pattern), pattern))

    def classify(
        self,
        text: str,
        *,
        trace_id: str,
        source: str = "unknown",
    ) -> ConstitutionalResult:
        normalized = self._normalize(text)
        if not normalized.strip():
            return ConstitutionalResult(is_violation=False)

        for rule, compiled, raw_pattern in self._compiled:
            if compiled.search(normalized):
                logger = get_security_logger()
                logger.warning(
                    "constitutional_violation_detected",
                    trace_id=trace_id,
                    source=source,
                    rule_id=rule.id,
                    severity=rule.severity,
                    confidence=rule.confidence,
                    matched_pattern=raw_pattern,
                )
                return ConstitutionalResult(
                    is_violation=True,
                    violated_rule=rule.id,
                    severity=rule.severity,
                    confidence=rule.confidence,
                    matched_pattern=raw_pattern,
                )

        return ConstitutionalResult(is_violation=False)

    def classify_many(
        self,
        texts: dict[str, str],
        *,
        trace_id: str,
    ) -> ConstitutionalResult:
        for source, text in texts.items():
            result = self.classify(text, trace_id=trace_id, source=source)
            if result.is_violation:
                return result
        return ConstitutionalResult(is_violation=False)

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text)
        return re.sub(r"\s+", " ", normalized)


def clear_rules_cache() -> None:
    """Clear cached rules — for tests only."""
    load_constitutional_rules.cache_clear()
