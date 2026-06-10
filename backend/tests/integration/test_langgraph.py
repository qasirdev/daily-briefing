"""Full LangGraph execution integration tests."""

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
from backend.mcp.calendar import CalendarMCPClient
from backend.mcp.postgres import PostgresMCPClient
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.security.token_budget import AGENT_TOKEN_BUDGETS, HARD_LIMIT_MULTIPLIER
from backend.settings import Settings
from backend.tests.conftest import MockMCPBundle


@pytest.mark.asyncio
async def test_graph_compiles_and_runs(
    mock_mcp: MockMCPBundle,
    mock_openrouter: AsyncMock,
) -> None:
    mcp = mock_mcp.as_clients()

    with (
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
        build_llm.return_value = mock_openrouter

        settings = Settings(enable_consensus_workflow=False)
        graph = build_briefing_graph(mcp, llm=mock_openrouter, settings=settings)
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

        with patch(
            "backend.agents.calendar.node.consent_store.has_valid_consent",
            return_value=True,
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


@pytest.mark.asyncio
async def test_critic_revision_routes_to_dlq_when_token_budget_exceeded(
    mock_mcp: MockMCPBundle,
) -> None:
    """Critic revision must not loop when per-agent token budget is exceeded (v2.0.0)."""
    mcp = mock_mcp.as_clients()
    trace_id = "d" * 32
    focus_over_hard_limit = AGENT_TOKEN_BUDGETS["focus"] * HARD_LIMIT_MULTIPLIER + 1
    metadata = ExecutionMetadata(
        execution_ms=1,
        tokens_used=focus_over_hard_limit,
        model_used="test",
        prompt_version="v2.0.0",
        trace_id=trace_id,
        data_classification="internal",
    )

    async def focus_over_budget(state: BriefingGraphState, llm: object) -> dict[str, object]:
        return {
            "focus_result": AgentResultEnvelope(
                agent_id="focus",
                canonical_role="planner",
                status="success",
                result={"plan": {"summary": "Work", "time_blocks": []}},
                metadata=metadata,
            ),
            "current_agent": "focus",
            "total_tokens": focus_over_hard_limit,
        }

    async def critic_requests_revision(state: BriefingGraphState, llm: object) -> dict[str, object]:
        revision_count = state.get("revision_count", 0) + 1
        return {
            "critic_result": AgentResultEnvelope(
                agent_id="critic",
                canonical_role="critic",
                status="success",
                result={
                    "approved": False,
                    "revision_required": True,
                    "issues": ["Plan needs more detail"],
                    "review_cycle": revision_count,
                },
                metadata=ExecutionMetadata(
                    execution_ms=1,
                    tokens_used=100,
                    model_used="test",
                    prompt_version="v2.0.0",
                    trace_id=trace_id,
                    data_classification="internal",
                ),
            ),
            "current_agent": "critic",
            "revision_count": revision_count,
        }

    with (
        patch("backend.graph.builder.focus_agent_node", side_effect=focus_over_budget),
        patch("backend.graph.builder.critic_agent_node", side_effect=critic_requests_revision),
        patch("backend.agents.calendar.node.consent_store.has_valid_consent", return_value=True),
    ):
        settings = Settings(enable_consensus_workflow=False)
        graph = build_briefing_graph(mcp, llm=AsyncMock(), settings=settings)
        initial_state: BriefingGraphState = {
            "user_id": "user-1",
            "request_id": "req-budget",
            "trace_id": trace_id,
            "requested_at": datetime.now(UTC),
            "target_date": date.today(),
            "current_agent": "",
            "revision_count": 0,
            "total_tokens": focus_over_hard_limit,
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
        result = await graph.ainvoke(initial_state)

    await mcp.close()
    assert result["status"] == "failure"
    assert result.get("failure_reason") == "token_budget_exceeded"
    assert result.get("dlq_events")


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


def test_graph_consensus_module_reexports_spec_path() -> None:
    from backend.graph import consensus as consensus_module

    assert hasattr(consensus_module, "consensus_evaluator_node")
    assert hasattr(consensus_module, "route_consensus")


@pytest.mark.asyncio
async def test_timeout_after_adversarial_does_not_bypass_critic_to_present() -> None:
    """Graph timeout must not present a briefing without Critic review (v2.0.0)."""
    postgres = PostgresMCPClient(host="localhost", port=5443)
    calendar = CalendarMCPClient(host="localhost", port=5444)
    mcp = MCPClients(postgres=postgres, calendar=calendar)
    present_mock = AsyncMock(
        return_value={
            "final_briefing": "bypassed",
            "status": "success",
            "current_agent": "orchestrator",
        },
    )

    success_meta = ExecutionMetadata(
        execution_ms=1,
        tokens_used=10,
        model_used="test",
        prompt_version="v2.0.0",
        trace_id="a" * 32,
        data_classification="internal",
    )
    verification_ok = AgentResultEnvelope(
        agent_id="verification",
        canonical_role="verifier",
        status="success",
        result={"issues": []},
        metadata=success_meta,
    )
    adversarial_ok = AgentResultEnvelope(
        agent_id="adversarial",
        canonical_role="critic",
        status="success",
        result={"concerns": []},
        metadata=success_meta,
    )

    with (
        patch.object(PostgresMCPClient, "query", AsyncMock(return_value={"rows": []})),
        patch.object(CalendarMCPClient, "get_events", AsyncMock(return_value=[])),
        patch("backend.agents.calendar.node.consent_store.has_valid_consent", return_value=True),
        patch(
            "backend.graph.builder.verification_agent_node",
            AsyncMock(
                return_value={
                    "verification_result": verification_ok,
                    "current_agent": "verification",
                },
            ),
        ),
        patch(
            "backend.graph.builder.adversarial_agent_node",
            AsyncMock(
                return_value={
                    "adversarial_result": adversarial_ok,
                    "current_agent": "adversarial",
                },
            ),
        ),
        patch("backend.graph.builder.orchestrator_present_node", present_mock),
        patch(
            "backend.graph.builder.focus_agent_node",
            AsyncMock(
                return_value={
                    "focus_result": _success_envelope("focus"),
                    "current_agent": "focus",
                    "total_tokens": 10,
                },
            ),
        ),
    ):
        settings = Settings(enable_consensus_workflow=True, graph_timeout_seconds=1)
        llm = AsyncMock()
        graph = build_briefing_graph(mcp, llm=llm, settings=settings)
        initial_state: BriefingGraphState = {
            "user_id": "user-1",
            "request_id": "req-timeout",
            "trace_id": "c" * 32,
            "requested_at": datetime.now(UTC),
            "target_date": date.today(),
            "current_agent": "",
            "revision_count": 0,
            "total_tokens": 10,
            "graph_started_at": time.perf_counter() - 5,
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
        result = await graph.ainvoke(initial_state)

    await mcp.close()
    present_mock.assert_not_called()
    assert result.get("critic_result") is None
    assert result.get("final_briefing") != "bypassed"


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
