"""Dead letter queue graph node."""

from __future__ import annotations

from typing import Any

import structlog

from backend.dependencies import PostgresMCPProtocol
from backend.dlq.store import dlq_store
from backend.graph.state import BriefingGraphState
from backend.schemas.dlq import DLQEvent
from backend.schemas.envelope import AgentResultEnvelope
from backend.security.failure_messages import failure_message_for
from backend.security.token_budget import evaluate_token_budget, is_session_token_exceeded
from backend.settings import get_settings

logger = structlog.get_logger()


def _resolve_reason(state: BriefingGraphState) -> str:
    existing = state.get("failure_reason")
    if isinstance(existing, str) and existing:
        return existing
    if evaluate_token_budget(state) == "token_budget_exceeded":
        return "token_budget_exceeded"
    settings = get_settings()
    if is_session_token_exceeded(state, configured_max=settings.token_budget_max):
        return "token_budget_exceeded"
    for key in (
        "input_security_result",
        "task_result",
        "calendar_result",
        "focus_result",
        "verification_result",
        "adversarial_result",
        "critic_result",
    ):
        envelope = state.get(key)
        if isinstance(envelope, AgentResultEnvelope) and envelope.status == "escalated":
            if envelope.escalation:
                return envelope.escalation.reason
    return "circuit_breaker"


def _resolve_envelope(state: BriefingGraphState) -> AgentResultEnvelope | None:
    agent = state.get("current_agent", "")
    if agent == "input_security_gate":
        gate = state.get("input_security_result")
        if isinstance(gate, AgentResultEnvelope):
            return gate
    if agent:
        envelope = state.get(f"{agent.replace('_agent', '')}_result")
        if isinstance(envelope, AgentResultEnvelope):
            return envelope
    for key in (
        "input_security_result",
        "critic_result",
        "verification_result",
        "adversarial_result",
        "focus_result",
        "task_result",
        "calendar_result",
    ):
        envelope = state.get(key)
        if isinstance(envelope, AgentResultEnvelope):
            return envelope
    return None


async def dlq_handler_node(
    state: BriefingGraphState,
    *,
    postgres: PostgresMCPProtocol | None = None,
) -> dict[str, Any]:
    """Record failed executions and terminate the graph."""
    trace_id = state.get("trace_id", "0" * 32)
    reason = _resolve_reason(state)
    message = state.get("failure_message") or failure_message_for(reason)
    agent_id = state.get("current_agent", "unknown").replace("_agent", "") or "unknown"

    event = DLQEvent(
        request_id=state.get("request_id", trace_id),
        user_id=state.get("user_id", "unknown"),
        agent_id=agent_id,
        reason=reason,  # type: ignore[arg-type]
        envelope=_resolve_envelope(state),
        trace_id=trace_id,
    )

    if postgres is not None:
        await dlq_store.persist(event, postgres=postgres)
    else:
        dlq_store.add(event)

    logger.error(
        "dlq_event_recorded",
        trace_id=trace_id,
        reason=reason,
        agent=agent_id,
        event_id=str(event.id),
    )

    events = list(state.get("dlq_events", []))
    events.append(
        {
            "id": str(event.id),
            "trace_id": trace_id,
            "reason": reason,
            "agent": agent_id,
        },
    )
    return {
        "status": "failure",
        "final_briefing": "",
        "dlq_events": events,
        "current_agent": "dlq_handler",
        "failure_reason": reason,
        "failure_message": message,
    }
