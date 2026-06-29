"""Reasoning trace observability tests (Gaps #67-68)."""

from __future__ import annotations

from backend.graph.state import BriefingGraphState
from backend.observability.reasoning_trace import collect_reasoning_traces
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata


def _envelope(agent_id: str, role: str) -> AgentResultEnvelope:
    return AgentResultEnvelope(
        agent_id=agent_id,
        canonical_role=role,  # type: ignore[arg-type]
        status="success",
        metadata=ExecutionMetadata(
            execution_ms=42,
            tokens_used=100,
            model_used="openai/gpt-4o-mini",
            prompt_version="v2.0.0",
            trace_id="a" * 32,
            data_classification="internal",
        ),
    )


def test_collect_reasoning_traces_from_agent_envelopes() -> None:
    state: BriefingGraphState = {
        "trace_id": "a" * 32,
        "task_result": _envelope("task", "doer"),
        "focus_result": _envelope("focus", "planner"),
    }
    trace = collect_reasoning_traces(state)
    assert trace.trace_id == "a" * 32
    assert len(trace.entries) == 2
    assert trace.entries[0].hitl_layer in ("execution", "planning")
    assert trace.hitl_mode == "human_on_the_loop"


def test_collect_human_escalation_trace() -> None:
    state: BriefingGraphState = {
        "trace_id": "b" * 32,
        "status": "awaiting_human_review",
        "consensus_result": {"major_concerns": 2},
    }
    trace = collect_reasoning_traces(state)
    assert trace.hitl_mode == "human_in_the_loop"
    assert any(entry.status == "awaiting_human" for entry in trace.entries)


def test_collect_revision_trace() -> None:
    state: BriefingGraphState = {
        "trace_id": "c" * 32,
        "revision_count": 2,
    }
    trace = collect_reasoning_traces(state)
    assert any(entry.hitl_layer == "revision" for entry in trace.entries)


def test_empty_state_returns_empty_entries() -> None:
    state: BriefingGraphState = {"trace_id": "d" * 32}
    trace = collect_reasoning_traces(state)
    assert trace.entries == []


def test_collect_input_security_gate_block_trace() -> None:
    blocked = AgentResultEnvelope(
        agent_id="input_security_gate",
        canonical_role="supervisor",
        status="escalated",
        result={"blocked_source": "calendar", "matched_pattern": "ignore_previous"},
        metadata=ExecutionMetadata(
            execution_ms=3,
            tokens_used=0,
            model_used="none",
            prompt_version="v2.0.0",
            trace_id="e" * 32,
            data_classification="internal",
        ),
        escalation=EscalationPayload(
            reason="security_violation_detected",
            target_agent="dlq_handler",
            context="ignore_previous",
        ),
    )
    state: BriefingGraphState = {
        "trace_id": "e" * 32,
        "task_result": _envelope("task", "doer"),
        "calendar_result": _envelope("calendar", "doer"),
        "input_security_result": blocked,
        "failure_reason": "security_violation_detected",
    }
    trace = collect_reasoning_traces(state)
    gate_entries = [entry for entry in trace.entries if entry.agent_id == "input_security_gate"]
    assert len(gate_entries) == 1
    assert gate_entries[0].status == "escalated"
    assert "security_violation_detected" in gate_entries[0].summary
