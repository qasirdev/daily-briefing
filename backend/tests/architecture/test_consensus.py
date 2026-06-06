"""Integration tests for multi-agent consensus workflow (Gaps #3-5)."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest

from backend.dependencies import MCPClients
from backend.graph.builder import build_briefing_graph
from backend.graph.state import BriefingGraphState
from backend.mcp.calendar import CalendarMCPClient
from backend.mcp.postgres import PostgresMCPClient
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.llm.models import LLMResponse
from backend.settings import Settings

TRACE_AGREEMENT = "a" * 32
TRACE_DISAGREEMENT = "b" * 32
TRACE_MINOR = "c" * 32


def _metadata(trace_id: str) -> ExecutionMetadata:
    return ExecutionMetadata(
        execution_ms=100,
        tokens_used=50,
        model_used="openai/gpt-4o",
        prompt_version="v1.0.0",
        trace_id=trace_id,
        data_classification="internal",
    )


def _focus_envelope(trace_id: str) -> AgentResultEnvelope:
    return AgentResultEnvelope(
        agent_id="focus",
        canonical_role="planner",
        status="success",
        result={
            "plan": {
                "summary": "Morning deep work, afternoon meetings",
                "time_blocks": [
                    {
                        "start": "09:00",
                        "end": "11:00",
                        "activity": "Complete Q2 report",
                        "priority": "high",
                        "type": "deep_work",
                    },
                ],
                "top_priorities": ["Complete Q2 report"],
            },
        },
        metadata=_metadata(trace_id),
    )


def _task_envelope(trace_id: str) -> AgentResultEnvelope:
    return AgentResultEnvelope(
        agent_id="task",
        canonical_role="doer",
        status="success",
        result={"tasks": [{"title": "Q2 report", "priority": "high"}]},
        metadata=_metadata(trace_id),
    )


def _calendar_envelope(trace_id: str) -> AgentResultEnvelope:
    return AgentResultEnvelope(
        agent_id="calendar",
        canonical_role="doer",
        status="success",
        result={"events": [{"summary": "Sprint Review", "start": "14:00"}]},
        metadata=_metadata(trace_id),
    )


def _base_state(trace_id: str) -> BriefingGraphState:
    return {
        "user_id": "test_user",
        "request_id": "test_request",
        "trace_id": trace_id,
        "requested_at": datetime.now(UTC),
        "target_date": date.today(),
        "current_agent": "",
        "revision_count": 0,
        "total_tokens": 0,
        "graph_started_at": time.perf_counter(),
        "final_briefing": None,
        "status": "pending",
        "consent_required": False,
        "consent_context": None,
        "consent_request": None,
        "dlq_events": [],
        "orchestrator_result": None,
        "task_result": None,
        "calendar_result": None,
        "focus_result": None,
        "verification_result": None,
        "adversarial_result": None,
        "consensus_result": None,
        "critic_result": None,
    }


@asynccontextmanager
async def _consensus_graph_patches(
    *,
    verification_return: dict[str, Any],
    adversarial_return: dict[str, Any],
    trace_id: str,
) -> AsyncIterator[Any]:
    """Patch upstream agents so integration tests isolate consensus routing."""
    mcp = MCPClients(
        postgres=PostgresMCPClient(host="localhost", port=5443),
        calendar=CalendarMCPClient(host="localhost", port=5444),
    )
    settings = Settings(enable_consensus_workflow=True)
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value=LLMResponse(
            content='{"approved": true, "issues": []}',
            model_used="test",
            tokens_used=5,
            latency_ms=1,
        ),
    )

    async def mock_task(state: BriefingGraphState, postgres: object) -> dict[str, Any]:
        return {"task_result": _task_envelope(trace_id), "current_agent": "task"}

    async def mock_calendar(state: BriefingGraphState, calendar: object) -> dict[str, Any]:
        return {"calendar_result": _calendar_envelope(trace_id), "current_agent": "calendar"}

    async def mock_focus(state: BriefingGraphState, llm_router: object) -> dict[str, Any]:
        return {"focus_result": _focus_envelope(trace_id), "current_agent": "focus", "total_tokens": 10}

    with (
        patch("backend.graph.builder.task_agent_node", side_effect=mock_task),
        patch("backend.graph.builder.calendar_agent_node", side_effect=mock_calendar),
        patch("backend.graph.builder.focus_agent_node", side_effect=mock_focus),
        patch(
            "backend.graph.builder.verification_agent_node",
            AsyncMock(return_value=verification_return),
        ),
        patch(
            "backend.graph.builder.adversarial_agent_node",
            AsyncMock(return_value=adversarial_return),
        ),
    ):
        graph = build_briefing_graph(mcp, llm=llm, settings=settings)
        try:
            yield graph
        finally:
            await mcp.close()


@pytest.mark.asyncio
async def test_consensus_agreement_path() -> None:
    """Graph routes to Critic when verification and adversarial agree."""
    verification_return = {
        "verification_result": AgentResultEnvelope(
            agent_id="verification",
            canonical_role="verifier",
            status="success",
            result={
                "status": "verified",
                "verified_claims": ["Plan matches MCP data"],
                "flagged_claims": [],
                "confidence": 1.0,
            },
            metadata=_metadata(TRACE_AGREEMENT),
        ),
        "current_agent": "verification",
    }
    adversarial_return = {
        "adversarial_result": AgentResultEnvelope(
            agent_id="adversarial",
            canonical_role="adversarial",
            status="success",
            result={
                "challenges": [],
                "risk_level": "low",
                "recommended_action": "approve",
            },
            metadata=_metadata(TRACE_AGREEMENT),
        ),
        "current_agent": "adversarial",
    }

    async with _consensus_graph_patches(
        verification_return=verification_return,
        adversarial_return=adversarial_return,
        trace_id=TRACE_AGREEMENT,
    ) as graph:
        result = await graph.ainvoke(_base_state(TRACE_AGREEMENT))

    assert result["status"] == "success"
    assert result.get("critic_result") is not None
    assert result["consensus_result"] is not None
    assert result["consensus_result"]["agreement_level"] == "agreement"


@pytest.mark.asyncio
async def test_consensus_disagreement_escalation() -> None:
    """Graph escalates to human review on major disagreement."""
    verification_return = {
        "verification_result": AgentResultEnvelope(
            agent_id="verification",
            canonical_role="verifier",
            status="escalated",
            result={
                "status": "discrepancies_found",
                "verified_claims": [],
                "flagged_claims": [
                    {
                        "claim": "Meeting at 3pm",
                        "issue": "Calendar shows 2pm",
                        "source_truth": "Meeting scheduled for 14:00",
                        "severity": "critical",
                    },
                    {
                        "claim": "High priority task due today",
                        "issue": "Task due date is tomorrow",
                        "source_truth": "Due date: 2026-06-05",
                        "severity": "critical",
                    },
                ],
                "confidence": 0.3,
            },
            metadata=_metadata(TRACE_DISAGREEMENT),
        ),
        "current_agent": "verification",
    }
    adversarial_return = {
        "adversarial_result": AgentResultEnvelope(
            agent_id="adversarial",
            canonical_role="adversarial",
            status="success",
            result={
                "challenges": [],
                "risk_level": "high",
                "recommended_action": "reject",
            },
            metadata=_metadata(TRACE_DISAGREEMENT),
        ),
        "current_agent": "adversarial",
    }

    async with _consensus_graph_patches(
        verification_return=verification_return,
        adversarial_return=adversarial_return,
        trace_id=TRACE_DISAGREEMENT,
    ) as graph:
        result = await graph.ainvoke(_base_state(TRACE_DISAGREEMENT))

    assert result["status"] == "awaiting_human_review"
    assert result["consensus_result"] is not None
    assert result["consensus_result"]["major_concerns"] >= 2
    assert result["consensus_result"]["agreement_level"] == "major_disagreement"
    assert result.get("critic_result") is None


@pytest.mark.asyncio
async def test_consensus_minor_disagreement_proceeds() -> None:
    """Graph proceeds to Critic when only moderate concerns are flagged."""
    verification_return = {
        "verification_result": AgentResultEnvelope(
            agent_id="verification",
            canonical_role="verifier",
            status="success",
            result={
                "status": "verified",
                "verified_claims": ["Claim 1", "Claim 2"],
                "flagged_claims": [
                    {
                        "claim": "Busy day ahead",
                        "issue": "Subjective assessment not in source",
                        "source_truth": "3 meetings scheduled",
                        "severity": "minor",
                    },
                ],
                "confidence": 0.85,
            },
            metadata=_metadata(TRACE_MINOR),
        ),
        "current_agent": "verification",
    }
    adversarial_return = {
        "adversarial_result": AgentResultEnvelope(
            agent_id="adversarial",
            canonical_role="adversarial",
            status="success",
            result={
                "challenges": [
                    {
                        "target": "Time estimate",
                        "concern": "May underestimate complexity",
                        "alternative": "Consider buffer time",
                        "severity": "moderate",
                    },
                ],
                "risk_level": "medium",
                "recommended_action": "request_clarification",
            },
            metadata=_metadata(TRACE_MINOR),
        ),
        "current_agent": "adversarial",
    }

    async with _consensus_graph_patches(
        verification_return=verification_return,
        adversarial_return=adversarial_return,
        trace_id=TRACE_MINOR,
    ) as graph:
        result = await graph.ainvoke(_base_state(TRACE_MINOR))

    assert result["status"] == "success"
    assert result.get("critic_result") is not None
    assert result["consensus_result"] is not None
    assert result["consensus_result"]["agreement_level"] == "minor_disagreement"
    assert result["consensus_result"]["moderate_concerns"] >= 1
    assert result["consensus_result"]["major_concerns"] == 0
