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
    focus_result: AgentResultEnvelope | None
    critic_result: AgentResultEnvelope | None

    current_agent: str
    revision_count: int
    total_tokens: int
    graph_started_at: float

    final_briefing: str | None
    status: Literal["pending", "success", "failure", "degraded", "awaiting_consent"]
    consent_required: bool
    consent_context: str | None
    consent_request: dict[str, object] | None
    dlq_events: list[dict[str, str]]
