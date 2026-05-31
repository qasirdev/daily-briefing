"""British date/time formatting tests."""

import pytest

from backend.agents.orchestrator.node import orchestrator_present_node
from backend.datetime_format import format_event_time_london, format_time_range
from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata


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
