"""LangGraph scaffold tests."""

from datetime import UTC, datetime

import pytest

from backend.graph.builder import build_briefing_graph
from backend.graph.state import BriefingGraphState


@pytest.mark.asyncio
async def test_graph_compiles_and_runs() -> None:
    graph = build_briefing_graph()
    initial_state: BriefingGraphState = {
        "user_id": "user-1",
        "request_id": "req-1",
        "trace_id": "b" * 32,
        "requested_at": datetime.now(UTC),
        "current_agent": "",
        "revision_count": 0,
        "total_tokens": 0,
        "status": "pending",
        "final_briefing": None,
        "orchestrator_result": None,
        "task_result": None,
        "calendar_result": None,
        "focus_result": None,
        "critic_result": None,
    }

    result = await graph.ainvoke(initial_state)

    assert result["status"] == "success"
    assert result["orchestrator_result"] is not None
    assert result["orchestrator_result"].agent_id == "orchestrator"
