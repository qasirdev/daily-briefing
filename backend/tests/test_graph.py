"""LangGraph scaffold tests."""

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.dependencies import MCPClients
from backend.graph.builder import build_briefing_graph, route_consensus
from backend.graph.state import BriefingGraphState
from backend.llm.models import LLMResponse
from backend.mcp.calendar import CalendarMCPClient
from backend.mcp.postgres import PostgresMCPClient
from backend.settings import Settings


@pytest.mark.asyncio
async def test_graph_compiles_and_runs() -> None:
    postgres = PostgresMCPClient(host="localhost", port=5443)  # default 5433
    calendar = CalendarMCPClient(host="localhost", port=5444)  # default 5434
    mcp = MCPClients(postgres=postgres, calendar=calendar)

    with (
        patch.object(
            PostgresMCPClient,
            "query",
            AsyncMock(return_value={"rows": []}),
        ),
        patch(
            "backend.graph.builder.focus_agent_node",
            AsyncMock(
                return_value={
                    "focus_result": None,
                    "current_agent": "focus",
                    "total_tokens": 0,
                },
            ),
        ),
        patch(
            "backend.graph.builder.build_llm_router",
        ) as build_llm,
    ):
        llm = AsyncMock()
        llm.generate = AsyncMock(
            return_value=LLMResponse(
                content='{"time_blocks": [], "summary": "Plan"}',
                model_used="test",
                tokens_used=5,
                latency_ms=1,
            ),
        )
        build_llm.return_value = llm

        graph = build_briefing_graph(mcp, llm=llm)
        initial_state: BriefingGraphState = {
            "user_id": "user-1",
            "request_id": "req-1",
            "trace_id": "b" * 32,
            "requested_at": datetime.now(UTC),
            "target_date": date.today(),
            "current_agent": "",
            "revision_count": 0,
            "total_tokens": 0,
            "graph_started_at": 0.0,
            "status": "pending",
            "final_briefing": None,
            "consent_required": False,
            "consent_context": None,
            "consent_request": None,
            "dlq_events": [],
            "orchestrator_result": None,
            "task_result": None,
            "calendar_result": None,
            "focus_result": None,
            "critic_result": None,
        }

        with patch.object(
            CalendarMCPClient,
            "get_events",
            AsyncMock(return_value=[]),
        ):
            result = await graph.ainvoke(initial_state)

    await mcp.close()
    assert result["status"] in {"success", "degraded", "failure", "pending"}


def test_route_consensus_major_disagreement() -> None:
    """Verify 2+ major concerns route to human escalation path."""
    state: BriefingGraphState = {
        "consensus_result": {
            "major_concerns": 2,
            "moderate_concerns": 0,
            "agreement_level": "major_disagreement",
        },
    }
    assert route_consensus(state) == "major_disagreement"


def test_route_consensus_minor_disagreement() -> None:
    """Verify moderate concerns proceed with warning path."""
    state: BriefingGraphState = {
        "consensus_result": {
            "major_concerns": 0,
            "moderate_concerns": 1,
            "agreement_level": "minor_disagreement",
        },
    }
    assert route_consensus(state) == "minor_disagreement"


@pytest.mark.asyncio
async def test_graph_compiles_with_consensus_enabled() -> None:
    """Verify consensus workflow graph compiles when feature flag is enabled."""
    postgres = PostgresMCPClient(host="localhost", port=5443)
    calendar = CalendarMCPClient(host="localhost", port=5444)
    mcp = MCPClients(postgres=postgres, calendar=calendar)
    settings = Settings(enable_consensus_workflow=True)
    llm = AsyncMock()

    graph = build_briefing_graph(mcp, llm=llm, settings=settings)
    assert graph is not None

    await mcp.close()
