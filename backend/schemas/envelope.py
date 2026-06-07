"""Canonical envelope for all inter-agent communication."""

from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

from backend.logging_config import get_security_logger
from backend.security.pii import PIIDetector


class GuardrailViolation(BaseModel):
    """Guardrail violation metadata for drift detection and security monitoring."""

    model_config = ConfigDict(strict=True, frozen=True)

    violation_type: str = Field(
        ...,
        description="Type of violation detected (e.g., prompt_injection_detected)",
    )
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ...,
        description="Violation severity level for alerting",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score from detection algorithm",
    )
    matched_pattern: str | None = Field(
        default=None,
        description="Regex pattern or signature that triggered detection",
    )
    context_snippet: str | None = Field(
        default=None,
        max_length=200,
        description="Truncated context showing where violation occurred",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When the violation was detected",
    )


class ExecutionMetadata(BaseModel):
    """Execution telemetry attached to every agent response."""

    model_config = ConfigDict(strict=True, frozen=True)

    execution_ms: int = Field(..., ge=0, le=300_000)
    tokens_used: int = Field(..., ge=0, le=128_000)
    cost_usd: float = Field(default=0.0, ge=0.0)
    model_used: str = Field(..., min_length=1)
    prompt_version: str = Field(..., pattern=r"^v\d+\.\d+\.\d+$")
    trace_id: str = Field(..., min_length=32, max_length=64)
    data_classification: Literal[
        "public",
        "internal",
        "confidential",
        "confidential_pii",
    ]
    guardrail_violations: list[GuardrailViolation] = Field(
        default_factory=list,
        description="Violations detected during agent execution",
    )
    violation_count: int = Field(
        default=0,
        ge=0,
        description="Total count of violations (cached for performance)",
    )


class EscalationPayload(BaseModel):
    """Escalation details when an agent cannot complete normally."""

    model_config = ConfigDict(strict=True, frozen=True)

    reason: Literal[
        "security_violation_detected",
        "max_retries_exceeded",
        "token_budget_exceeded",
        "mcp_timeout",
        "consent_required",
        "unexpected_error",
    ]
    target_agent: str = "orchestrator"
    context: str = ""


class AgentResultEnvelope(BaseModel):
    """Canonical envelope returned by every LangGraph agent node."""

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    agent_id: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z_]+$")
    canonical_role: Literal[
        "doer",
        "planner",
        "critic",
        "tool_operator",
        "supervisor",
        "verifier",
        "adversarial",
    ]
    status: Literal["success", "failure", "escalated"]
    result: dict[str, object] | None = None
    metadata: ExecutionMetadata
    escalation: EscalationPayload | None = None

    @field_validator("result")
    @classmethod
    def validate_result_for_success(
        cls,
        value: dict[str, object] | None,
        info: ValidationInfo,
    ) -> dict[str, object] | None:
        status = info.data.get("status")
        if status == "success" and value is None:
            msg = "result is required when status is success"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def warn_on_unmasked_pii(self) -> Self:
        detector = PIIDetector()
        texts: list[str] = []
        if self.escalation is not None:
            texts.append(self.escalation.context)
        if self.result is not None:
            for item in self.result.values():
                if isinstance(item, str):
                    texts.append(item)
        for text in texts:
            if detector.contains_pii(text):
                get_security_logger().warning(
                    "unmasked_pii_in_envelope",
                    agent_id=self.agent_id,
                    data_classification=self.metadata.data_classification,
                )
                break
        return self
