"""Orchestrator consent handling tests."""

import pytest

from backend.agents.orchestrator.node import build_consent_prompt, orchestrator_present_node
from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata


def _envelope(**kwargs: object) -> AgentResultEnvelope:
    defaults = {
        "agent_id": "calendar",
        "canonical_role": "doer",
        "status": "escalated",
        "metadata": ExecutionMetadata(
            execution_ms=1,
            tokens_used=0,
            model_used="none",
            prompt_version="v1.5.0",
            trace_id="d" * 32,
            data_classification="internal",
        ),
    }
    defaults.update(kwargs)
    return AgentResultEnvelope(**defaults)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_orchestrator_returns_consent_request() -> None:
    state: BriefingGraphState = {
        "user_id": "user-1",
        "request_id": "req-1",
        "trace_id": "d" * 32,
        "consent_required": True,
        "consent_context": "Google Calendar consent required",
        "calendar_result": _envelope(
            escalation=EscalationPayload(
                reason="consent_required",
                target_agent="orchestrator",
                context='{"service":"google_calendar","scope":["calendar.readonly"],"suggested_ttl_hours":4}',
            ),
        ),
    }
    update = await orchestrator_present_node(state)
    assert update["status"] == "awaiting_consent"
    assert update.get("consent_request") is not None


def test_build_consent_prompt_from_escalation() -> None:
    state: BriefingGraphState = {
        "request_id": "req-2",
        "trace_id": "e" * 32,
        "calendar_result": _envelope(
            escalation=EscalationPayload(
                reason="consent_required",
                target_agent="orchestrator",
                context='{"service":"google_calendar","scope":["calendar.readonly"],"suggested_ttl_hours":4}',
            ),
        ),
    }
    prompt = build_consent_prompt(state)
    assert prompt.service == "google_calendar"
    assert prompt.suggested_ttl_hours == 4
