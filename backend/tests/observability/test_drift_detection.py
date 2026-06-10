"""Tests for rogue agent drift detection (Gap #99)."""

import pytest
from pydantic import ValidationError

from backend.observability.metrics import GUARDRAIL_VIOLATIONS, log_guardrail_violation
from backend.schemas.envelope import ExecutionMetadata, GuardrailViolation


def test_guardrail_violation_logging() -> None:
    """Verify log_guardrail_violation increments the Prometheus counter."""
    violation = GuardrailViolation(
        violation_type="prompt_injection_detected",
        severity="critical",
        confidence=0.95,
        matched_pattern="ignore_previous",
    )

    initial_count = GUARDRAIL_VIOLATIONS.labels(
        agent_id="critic",
        violation_type="prompt_injection_detected",
        severity="critical",
    )._value.get()

    log_guardrail_violation(
        trace_id="test_trace_123",
        agent_id="critic",
        violation=violation,
    )

    final_count = GUARDRAIL_VIOLATIONS.labels(
        agent_id="critic",
        violation_type="prompt_injection_detected",
        severity="critical",
    )._value.get()

    assert final_count == initial_count + 1


def test_execution_metadata_with_violations() -> None:
    """Verify ExecutionMetadata includes violation tracking fields."""
    metadata = ExecutionMetadata(
        execution_ms=1234,
        tokens_used=512,
        model_used="openai/gpt-4o-mini",
        prompt_version="v1.5.0",
        trace_id="a" * 32,
        data_classification="internal",
        guardrail_violations=[
            GuardrailViolation(
                violation_type="token_budget_exceeded",
                severity="high",
                confidence=1.0,
            ),
        ],
        violation_count=1,
    )

    assert metadata.violation_count == 1
    assert len(metadata.guardrail_violations) == 1
    assert metadata.guardrail_violations[0].violation_type == "token_budget_exceeded"


def test_guardrail_violation_immutability() -> None:
    """Verify GuardrailViolation is frozen and cannot be mutated."""
    violation = GuardrailViolation(
        violation_type="unauthorized_tool_access",
        severity="critical",
        confidence=1.0,
    )

    with pytest.raises(ValidationError):
        violation.severity = "low"  # type: ignore[misc]


def test_execution_metadata_immutability() -> None:
    """Verify ExecutionMetadata is frozen and cannot be mutated."""
    metadata = ExecutionMetadata(
        execution_ms=1000,
        tokens_used=100,
        model_used="openai/gpt-4o",
        prompt_version="v1.0.0",
        trace_id="b" * 32,
        data_classification="public",
    )

    with pytest.raises(ValidationError):
        metadata.tokens_used = 200  # type: ignore[misc]


def test_violation_confidence_bounds() -> None:
    """Verify violation confidence is constrained to [0.0, 1.0]."""
    GuardrailViolation(
        violation_type="test",
        severity="low",
        confidence=0.0,
    )
    GuardrailViolation(
        violation_type="test",
        severity="low",
        confidence=1.0,
    )

    with pytest.raises(ValidationError):
        GuardrailViolation(
            violation_type="test",
            severity="low",
            confidence=1.5,
        )

    with pytest.raises(ValidationError):
        GuardrailViolation(
            violation_type="test",
            severity="low",
            confidence=-0.1,
        )


def test_violation_severity_literal() -> None:
    """Verify only valid severity literals are accepted."""
    for severity in ("low", "medium", "high", "critical"):
        GuardrailViolation(
            violation_type="test",
            severity=severity,
            confidence=0.5,
        )

    with pytest.raises(ValidationError):
        GuardrailViolation(
            violation_type="test",
            severity="urgent",  # type: ignore[arg-type]
            confidence=0.5,
        )


def test_context_snippet_max_length() -> None:
    """Verify context_snippet is truncated to 200 characters."""
    GuardrailViolation(
        violation_type="test",
        severity="low",
        confidence=0.5,
        context_snippet="x" * 200,
    )

    with pytest.raises(ValidationError):
        GuardrailViolation(
            violation_type="test",
            severity="low",
            confidence=0.5,
            context_snippet="x" * 201,
        )
