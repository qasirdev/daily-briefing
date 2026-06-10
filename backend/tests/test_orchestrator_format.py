"""British date/time formatting tests."""

import pytest

from backend.agents.orchestrator.node import orchestrator_present_node
from backend.datetime_format import format_event_time_london, format_time_range
from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import (
    AgentResultEnvelope,
    EscalationPayload,
    ExecutionMetadata,
)


def test_format_event_time_london() -> None:
    assert format_event_time_london("2026-05-31T20:00:00+01:00") == "31-05-2026 at 20:00"
    assert format_event_time_london("2026-06-03") == "03-06-2026"


def test_format_time_range_same_day() -> None:
    assert format_time_range("2026-05-31T20:00:00+01:00", "2026-05-31T21:00:00+01:00") == (
        "31-05-2026 at 20:00 – 21:00"
    )


@pytest.mark.asyncio
async def test_orchestrator_uses_formatted_calendar_events() -> None:
    state: BriefingGraphState = {
        "trace_id": "b" * 32,
        "calendar_result": AgentResultEnvelope(
            agent_id="calendar",
            canonical_role="doer",
            status="success",
            result={"events": [{"summary": "Interview", "start": "31-05-2026 at 20:00"}]},
            metadata=ExecutionMetadata(
                execution_ms=1,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id="b" * 32,
                data_classification="internal",
            ),
        ),
    }
    briefing = (await orchestrator_present_node(state))["final_briefing"]
    assert briefing is not None
    assert "31-05-2026 at 20:00" in briefing


@pytest.mark.asyncio
async def test_orchestrator_masks_labelled_pii_in_calendar_events() -> None:
    state: BriefingGraphState = {
        "trace_id": "b" * 32,
        "calendar_result": AgentResultEnvelope(
            agent_id="calendar",
            canonical_role="doer",
            status="success",
            result={
                "events": [
                    {
                        "summary": (
                            "AI Engineer Interview with full name: Qasir Mehmood , dob: 01/01/1990"
                        ),
                        "start": "10-06-2026 at 14:00",
                    },
                ],
            },
            metadata=ExecutionMetadata(
                execution_ms=1,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id="b" * 32,
                data_classification="internal",
            ),
        ),
    }
    briefing = (await orchestrator_present_node(state))["final_briefing"]
    assert briefing is not None
    assert "Qasir Mehmood" not in briefing
    assert "01/01/1990" not in briefing
    assert "[REDACTED_NAME]" in briefing


@pytest.mark.asyncio
async def test_orchestrator_marks_briefing_degraded_when_focus_escalates() -> None:
    state: BriefingGraphState = {
        "trace_id": "b" * 32,
        "calendar_result": AgentResultEnvelope(
            agent_id="calendar",
            canonical_role="doer",
            status="success",
            result={"events": [{"summary": "Team sync", "start": "10-06-2026 at 10:00"}]},
            metadata=ExecutionMetadata(
                execution_ms=1,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id="b" * 32,
                data_classification="internal",
            ),
        ),
        "focus_result": AgentResultEnvelope(
            agent_id="focus",
            canonical_role="planner",
            status="escalated",
            escalation=EscalationPayload(
                reason="max_retries_exceeded",
                target_agent="orchestrator",
                context='{"stage":"parse_or_validate","errors":["Response is not valid JSON"]}',
            ),
            metadata=ExecutionMetadata(
                execution_ms=1,
                tokens_used=120,
                model_used="deepseek/deepseek-v4-flash",
                prompt_version="v2.0.0",
                trace_id="b" * 32,
                data_classification="confidential",
            ),
        ),
    }
    update = await orchestrator_present_node(state)
    assert update["status"] == "degraded"
    assert "Focus Plan" not in (update["final_briefing"] or "")
    assert "degraded" in (update["final_briefing"] or "").lower()
