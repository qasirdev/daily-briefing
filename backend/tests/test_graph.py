"""LangGraph scaffold tests."""

import time
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.dependencies import MCPClients
from backend.graph.builder import (
    _is_graph_timeout,
    build_briefing_graph,
    route_consensus,
    should_circuit_break,
    should_route_to_dlq,
)
from backend.graph.state import BriefingGraphState
from backend.llm.models import LLMResponse
from backend.mcp.calendar import CalendarMCPClient
from backend.mcp.postgres import PostgresMCPClient
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
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

        settings = Settings(enable_consensus_workflow=False)
        graph = build_briefing_graph(mcp, llm=llm, settings=settings)
        initial_state: BriefingGraphState = {
            "user_id": "user-1",
            "request_id": "req-1",
            "trace_id": "b" * 32,
            "requested_at": datetime.now(UTC),
            "target_date": date.today(),
            "current_agent": "",
            "revision_count": 0,
            "total_tokens": 0,
            "graph_started_at": time.perf_counter(),
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

        with (
            patch.object(
                CalendarMCPClient,
                "get_events",
                AsyncMock(return_value=[]),
            ),
            patch(
                "backend.agents.calendar.node.consent_store.has_valid_consent",
                return_value=True,
            ),
        ):
            result = await graph.ainvoke(initial_state)

    await mcp.close()
    assert result["status"] in {"success", "degraded", "failure", "pending"}


def _success_envelope(agent_id: str) -> AgentResultEnvelope:
    return AgentResultEnvelope(
        agent_id=agent_id,
        canonical_role="doer",
        status="success",
        result={"ok": True},
        metadata=ExecutionMetadata(
            execution_ms=1,
            tokens_used=18_146,
            model_used="openai/gpt-4o-mini",
            prompt_version="v1.5.0",
            trace_id="f" * 32,
            data_classification="internal",
        ),
    )


def test_graph_timeout_triggers_dlq_route() -> None:
    settings = Settings(graph_timeout_seconds=60)
    state: BriefingGraphState = {
        "graph_started_at": time.perf_counter() - 61,
        "focus_result": _success_envelope("focus"),
    }
    assert _is_graph_timeout(state, settings) is True
    assert should_route_to_dlq(state, settings) is True


def test_revision_loop_session_tokens_do_not_abort_to_dlq() -> None:
    settings = Settings(token_budget_max=16_000)
    state: BriefingGraphState = {
        "total_tokens": 36_257,
        "focus_result": _success_envelope("focus"),
    }
    assert should_circuit_break(state, settings) is False
    assert should_route_to_dlq(state, settings) is False


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
