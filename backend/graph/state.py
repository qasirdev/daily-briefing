"""LangGraph shared state definition."""

from datetime import datetime
from typing import Literal, TypedDict

from backend.schemas.envelope import AgentResultEnvelope


class BriefingGraphState(TypedDict, total=False):
    """Shared state across the agent graph."""

    user_id: str
    request_id: str
    trace_id: str
    requested_at: datetime

    orchestrator_result: AgentResultEnvelope | None
    task_result: AgentResultEnvelope | None
    calendar_result: AgentResultEnvelope | None
    focus_result: AgentResultEnvelope | None
    critic_result: AgentResultEnvelope | None

    current_agent: str
    revision_count: int
    total_tokens: int

    final_briefing: str | None
    status: Literal["pending", "success", "failure", "degraded"]
