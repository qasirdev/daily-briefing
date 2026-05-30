"""Canonical envelope for all inter-agent communication."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class ExecutionMetadata(BaseModel):
    """Execution telemetry attached to every agent response."""

    model_config = ConfigDict(strict=True, frozen=True)

    execution_ms: int = Field(..., ge=0, le=300_000)
    tokens_used: int = Field(..., ge=0, le=128_000)
    model_used: str = Field(..., min_length=1)
    prompt_version: str = Field(..., pattern=r"^v\d+\.\d+\.\d+$")
    trace_id: str = Field(..., min_length=32, max_length=64)
    data_classification: Literal[
        "public",
        "internal",
        "confidential",
        "confidential_pii",
    ]


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
    canonical_role: Literal["doer", "planner", "critic", "tool_operator", "supervisor"]
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
