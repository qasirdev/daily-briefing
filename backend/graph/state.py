"""LangGraph shared state definition."""

from datetime import date, datetime
from typing import Literal, TypedDict

from backend.schemas.envelope import AgentResultEnvelope


class BriefingGraphState(TypedDict, total=False):
    """Shared state across the agent graph."""

    user_id: str
    request_id: str
    trace_id: str
    requested_at: datetime
    target_date: date

    orchestrator_result: AgentResultEnvelope | None
    task_result: AgentResultEnvelope | None
    calendar_result: AgentResultEnvelope | None
    input_security_result: AgentResultEnvelope | None
    focus_result: AgentResultEnvelope | None
    verification_result: AgentResultEnvelope | None
    adversarial_result: AgentResultEnvelope | None
    consensus_result: dict[str, object] | None
    critic_result: AgentResultEnvelope | None

    current_agent: str
    revision_count: int
    verification_retry_count: int
    adversarial_retry_count: int
    regeneration_constraints: str | None
    total_tokens: int
    graph_started_at: float

    working_memory_tokens: int
    working_memory_limit: int
    working_memory_context: list[str]

    final_briefing: str | None
    status: Literal[
        "pending",
        "success",
        "failure",
        "degraded",
        "awaiting_consent",
        "awaiting_human_review",
    ]
    consent_required: bool
    consent_context: str | None
    consent_request: dict[str, object] | None
    dlq_events: list[dict[str, str]]
    failure_reason: str | None
    failure_message: str | None
