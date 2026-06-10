"""Collect reasoning traces from LangGraph state (Gaps #67-68)."""

from __future__ import annotations

from typing import Literal

from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope
from backend.schemas.reasoning_trace import HitlLayerId, ReasoningTraceEntry, ReasoningTraceResponse

_AGENT_LAYER_MAP: dict[str, HitlLayerId] = {
    "orchestrator": "input",
    "task": "execution",
    "calendar": "execution",
    "focus": "planning",
    "verification": "review",
    "adversarial": "review",
    "critic": "review",
    "input_security_gate": "input",
    "human_escalation": "override",
}

_AGENT_STATE_KEYS: tuple[tuple[str, str], ...] = (
    ("orchestrator", "orchestrator_result"),
    ("task", "task_result"),
    ("calendar", "calendar_result"),
    ("input_security_gate", "input_security_result"),
    ("focus", "focus_result"),
    ("verification", "verification_result"),
    ("adversarial", "adversarial_result"),
    ("critic", "critic_result"),
)


def _summary_for_envelope(agent_id: str, envelope: AgentResultEnvelope) -> str:
    if envelope.escalation is not None:
        return f"{agent_id}: escalated ({envelope.escalation.reason})"
    if envelope.status == "failure":
        return f"{agent_id}: failed execution"
    return f"{agent_id}: completed ({envelope.canonical_role})"


def collect_reasoning_traces(state: BriefingGraphState) -> ReasoningTraceResponse:
    """Build reasoning trace entries from agent envelopes in graph state."""
    trace_id = state.get("trace_id", "0" * 32)
    entries: list[ReasoningTraceEntry] = []

    for agent_id, state_key in _AGENT_STATE_KEYS:
        envelope = state.get(state_key)
        if not isinstance(envelope, AgentResultEnvelope):
            continue
        layer = _AGENT_LAYER_MAP.get(agent_id, "monitoring")
        status = envelope.status
        if envelope.escalation and envelope.escalation.reason == "consent_required":
            status = "escalated"
        entries.append(
            ReasoningTraceEntry(
                agent_id=agent_id,
                hitl_layer=layer,
                summary=_summary_for_envelope(agent_id, envelope),
                status=status,
                tokens_used=envelope.metadata.tokens_used,
                execution_ms=envelope.metadata.execution_ms,
            ),
        )

    graph_status = state.get("status")
    if graph_status == "awaiting_human_review":
        consensus = state.get("consensus_result") or {}
        entries.append(
            ReasoningTraceEntry(
                agent_id="human_escalation",
                hitl_layer="override",
                summary=(
                    "Consensus disagreement requires human review "
                    f"(major_concerns={consensus.get('major_concerns', 0)})"
                ),
                status="awaiting_human",
            ),
        )

    revision_count = state.get("revision_count", 0)
    if revision_count > 0:
        entries.append(
            ReasoningTraceEntry(
                agent_id="critic",
                hitl_layer="revision",
                summary=f"Critic revision loop executed {revision_count} time(s)",
                status="success",
            ),
        )

    hitl_mode: Literal["human_on_the_loop", "human_in_the_loop"] = (
        "human_in_the_loop" if graph_status == "awaiting_human_review" else "human_on_the_loop"
    )
    return ReasoningTraceResponse(
        trace_id=trace_id,
        entries=entries,
        hitl_mode=hitl_mode,
    )
