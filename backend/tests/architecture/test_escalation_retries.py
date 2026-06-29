"""Tests for verification_failed and adversarial_concerns retry routing."""

from __future__ import annotations

import json
import time
from datetime import UTC, date, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.adversarial.node import adversarial_agent_node
from backend.agents.verification.node import verification_agent_node
from backend.dependencies import MCPClients
from backend.graph.builder import (
    MAX_ADVERSARIAL_REGENERATIONS,
    MAX_VERIFICATION_RETRIES,
    build_briefing_graph,
)
from backend.graph.state import BriefingGraphState
from backend.mcp.calendar import CalendarMCPClient
from backend.mcp.postgres import PostgresMCPClient
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata
from backend.settings import Settings


def _metadata() -> ExecutionMetadata:
    return ExecutionMetadata(
        execution_ms=1,
        tokens_used=0,
        model_used="none",
        prompt_version="v2.0.0",
        trace_id="f" * 32,
        data_classification="internal",
    )


def _base_state(**overrides: object) -> BriefingGraphState:
    state: BriefingGraphState = {
        "user_id": "user-1",
        "request_id": "req-1",
        "trace_id": "f" * 32,
        "requested_at": datetime.now(UTC),
        "target_date": date.today(),
        "revision_count": 0,
        "verification_retry_count": 0,
        "adversarial_retry_count": 0,
        "regeneration_constraints": None,
        "total_tokens": 0,
        "graph_started_at": time.perf_counter(),
        "status": "pending",
        "final_briefing": None,
        "consent_required": False,
        "consent_context": None,
        "consent_request": None,
        "dlq_events": [],
        "current_agent": "",
        "focus_result": AgentResultEnvelope(
            agent_id="focus",
            canonical_role="planner",
            status="success",
            result={"plan": {"summary": "Work", "time_blocks": []}},
            metadata=_metadata(),
        ),
        "task_result": None,
        "calendar_result": None,
        "verification_result": None,
        "adversarial_result": None,
        "consensus_result": None,
        "critic_result": None,
        "orchestrator_result": None,
    }
    state.update(overrides)  # type: ignore[typeddict-item]
    return state


@pytest.mark.asyncio
async def test_verification_escalates_with_verification_failed_reason() -> None:
    state = _base_state()
    state["focus_result"] = AgentResultEnvelope(
        agent_id="focus",
        canonical_role="planner",
        status="success",
        result={"plan": "not-a-dict"},
        metadata=_metadata(),
    )
    update = await verification_agent_node(state, llm=None)
    envelope = update["verification_result"]
    assert isinstance(envelope, AgentResultEnvelope)
    assert envelope.status == "escalated"
    assert envelope.escalation is not None
    assert envelope.escalation.reason == "verification_failed"
    assert envelope.escalation.retry_allowed is True
    assert update.get("regeneration_constraints")


@pytest.mark.asyncio
async def test_adversarial_escalates_with_adversarial_concerns() -> None:
    state = _base_state(
        verification_result=AgentResultEnvelope(
            agent_id="verification",
            canonical_role="verifier",
            status="escalated",
            result={
                "status": "discrepancies_found",
                "flagged_claims": [
                    {
                        "claim": "Meeting time",
                        "issue": "Mismatch",
                        "source_truth": "14:00",
                        "severity": "critical",
                    },
                ],
                "verified_claims": [],
                "confidence": 0.2,
            },
            metadata=_metadata(),
        ),
    )
    update = await adversarial_agent_node(state, llm=None)
    envelope = update["adversarial_result"]
    assert isinstance(envelope, AgentResultEnvelope)
    assert envelope.status == "escalated"
    assert envelope.escalation is not None
    assert envelope.escalation.reason == "adversarial_concerns"
    assert update.get("regeneration_constraints")


def test_builder_retry_limits_match_spec() -> None:
    assert MAX_VERIFICATION_RETRIES == 1
    assert MAX_ADVERSARIAL_REGENERATIONS == 1


@pytest.mark.asyncio
async def test_verification_retry_routes_back_to_focus_once() -> None:
    trace_id = "g" * 32
    focus_calls = 0
    verification_calls = 0

    async def counting_focus(state: BriefingGraphState, llm: object) -> dict[str, Any]:
        nonlocal focus_calls
        focus_calls += 1
        return {
            "focus_result": AgentResultEnvelope(
                agent_id="focus",
                canonical_role="planner",
                status="success",
                result={"plan": {"summary": "Retry plan", "time_blocks": []}},
                metadata=_metadata(),
            ),
            "current_agent": "focus",
        }

    def verification_return() -> dict[str, Any]:
        nonlocal verification_calls
        verification_calls += 1
        if verification_calls > 1:
            return {
                "verification_result": AgentResultEnvelope(
                    agent_id="verification",
                    canonical_role="verifier",
                    status="success",
                    result={
                        "status": "verified",
                        "flagged_claims": [],
                        "verified_claims": ["Retry plan"],
                        "confidence": 0.95,
                    },
                    metadata=_metadata(),
                ),
                "current_agent": "verification",
            }
        return {
            "verification_result": AgentResultEnvelope(
                agent_id="verification",
                canonical_role="verifier",
                status="escalated",
                result={
                    "status": "discrepancies_found",
                    "flagged_claims": [
                        {
                            "claim": "Task count",
                            "issue": "Mismatch",
                            "source_truth": "3 tasks",
                            "severity": "critical",
                        },
                    ],
                    "verified_claims": [],
                    "confidence": 0.4,
                },
                escalation=EscalationPayload(
                    reason="verification_failed",
                    target_agent="focus",
                    context=json.dumps({"flagged_claims": []}),
                    retry_allowed=True,
                ),
                metadata=_metadata(),
            ),
            "current_agent": "verification",
            "regeneration_constraints": json.dumps({"flagged_claims": []}),
        }

    adversarial_return = {
        "adversarial_result": AgentResultEnvelope(
            agent_id="adversarial",
            canonical_role="adversarial",
            status="success",
            result={"challenges": [], "risk_level": "low", "recommended_action": "approve"},
            metadata=_metadata(),
        ),
        "current_agent": "adversarial",
    }

    mcp = MCPClients(
        postgres=PostgresMCPClient(host="localhost", port=5443),
        calendar=CalendarMCPClient(host="localhost", port=5444),
    )
    settings = Settings(enable_consensus_workflow=True)

    async def mock_task(state: BriefingGraphState, postgres: object) -> dict[str, Any]:
        return {
            "task_result": AgentResultEnvelope(
                agent_id="task",
                canonical_role="doer",
                status="success",
                result={"tasks": []},
                metadata=_metadata(),
            ),
            "current_agent": "task",
        }

    async def mock_calendar(state: BriefingGraphState, calendar: object) -> dict[str, Any]:
        return {
            "calendar_result": AgentResultEnvelope(
                agent_id="calendar",
                canonical_role="tool_operator",
                status="success",
                result={"events": []},
                metadata=_metadata(),
            ),
            "current_agent": "calendar",
        }

    async def mock_critic(state: BriefingGraphState, llm: object) -> dict[str, Any]:
        return {
            "critic_result": AgentResultEnvelope(
                agent_id="critic",
                canonical_role="critic",
                status="success",
                result={"approved": True, "issues": [], "revision_required": False},
                metadata=_metadata(),
            ),
            "current_agent": "critic",
        }

    with (
        patch("backend.graph.builder.task_agent_node", side_effect=mock_task),
        patch("backend.graph.builder.calendar_agent_node", side_effect=mock_calendar),
        patch("backend.graph.builder.focus_agent_node", side_effect=counting_focus),
        patch("backend.graph.builder.critic_agent_node", side_effect=mock_critic),
        patch(
            "backend.graph.builder.verification_agent_node",
            AsyncMock(side_effect=lambda *_a, **_k: verification_return()),
        ),
        patch(
            "backend.graph.builder.adversarial_agent_node",
            AsyncMock(return_value=adversarial_return),
        ),
    ):
        graph = build_briefing_graph(mcp, llm=AsyncMock(), settings=settings)
        result = await graph.ainvoke(_base_state(trace_id=trace_id))

    assert focus_calls == 2
    assert verification_calls == 2
    assert result.get("verification_retry_count", 0) >= 1
    assert result.get("critic_result") is not None


@pytest.mark.asyncio
async def test_focus_escalation_routes_to_dlq() -> None:
    trace_id = "h" * 32

    async def escalated_focus(state: BriefingGraphState, llm: object) -> dict[str, Any]:
        return {
            "focus_result": AgentResultEnvelope(
                agent_id="focus",
                canonical_role="planner",
                status="escalated",
                escalation=EscalationPayload(
                    reason="max_retries_exceeded",
                    target_agent="orchestrator",
                    context='{"stage":"parse_or_validate","errors":["invalid"]}',
                ),
                metadata=_metadata(),
            ),
            "current_agent": "focus",
        }

    mcp = MCPClients(
        postgres=PostgresMCPClient(host="localhost", port=5443),
        calendar=CalendarMCPClient(host="localhost", port=5444),
    )
    settings = Settings(enable_consensus_workflow=True)

    async def mock_task(state: BriefingGraphState, postgres: object) -> dict[str, Any]:
        return {
            "task_result": AgentResultEnvelope(
                agent_id="task",
                canonical_role="doer",
                status="success",
                result={"tasks": []},
                metadata=_metadata(),
            ),
            "current_agent": "task",
        }

    async def mock_calendar(state: BriefingGraphState, calendar: object) -> dict[str, Any]:
        return {
            "calendar_result": AgentResultEnvelope(
                agent_id="calendar",
                canonical_role="tool_operator",
                status="success",
                result={"events": []},
                metadata=_metadata(),
            ),
            "current_agent": "calendar",
        }

    with (
        patch("backend.graph.builder.task_agent_node", side_effect=mock_task),
        patch("backend.graph.builder.calendar_agent_node", side_effect=mock_calendar),
        patch("backend.graph.builder.focus_agent_node", side_effect=escalated_focus),
    ):
        graph = build_briefing_graph(mcp, llm=AsyncMock(), settings=settings)
        result = await graph.ainvoke(_base_state(trace_id=trace_id))

    assert result["status"] == "failure"
    assert result.get("failure_reason") == "max_retries_exceeded"
    assert result.get("dlq_events")
    assert result.get("critic_result") is None


@pytest.mark.asyncio
async def test_verification_exhausted_retries_route_to_dlq() -> None:
    trace_id = "i" * 32
    focus_calls = 0

    async def counting_focus(state: BriefingGraphState, llm: object) -> dict[str, Any]:
        nonlocal focus_calls
        focus_calls += 1
        return {
            "focus_result": AgentResultEnvelope(
                agent_id="focus",
                canonical_role="planner",
                status="success",
                result={"plan": {"summary": "Retry plan", "time_blocks": []}},
                metadata=_metadata(),
            ),
            "current_agent": "focus",
        }

    verification_return = {
        "verification_result": AgentResultEnvelope(
            agent_id="verification",
            canonical_role="verifier",
            status="escalated",
            result={
                "status": "discrepancies_found",
                "flagged_claims": [
                    {
                        "claim": "Task count",
                        "issue": "Mismatch",
                        "source_truth": "3 tasks",
                        "severity": "critical",
                    },
                ],
                "verified_claims": [],
                "confidence": 0.4,
            },
            escalation=EscalationPayload(
                reason="verification_failed",
                target_agent="focus",
                context=json.dumps({"flagged_claims": []}),
                retry_allowed=True,
            ),
            metadata=_metadata(),
        ),
        "current_agent": "verification",
        "regeneration_constraints": json.dumps({"flagged_claims": []}),
    }

    mcp = MCPClients(
        postgres=PostgresMCPClient(host="localhost", port=5443),
        calendar=CalendarMCPClient(host="localhost", port=5444),
    )
    settings = Settings(enable_consensus_workflow=True)

    async def mock_task(state: BriefingGraphState, postgres: object) -> dict[str, Any]:
        return {
            "task_result": AgentResultEnvelope(
                agent_id="task",
                canonical_role="doer",
                status="success",
                result={"tasks": []},
                metadata=_metadata(),
            ),
            "current_agent": "task",
        }

    async def mock_calendar(state: BriefingGraphState, calendar: object) -> dict[str, Any]:
        return {
            "calendar_result": AgentResultEnvelope(
                agent_id="calendar",
                canonical_role="tool_operator",
                status="success",
                result={"events": []},
                metadata=_metadata(),
            ),
            "current_agent": "calendar",
        }

    with (
        patch("backend.graph.builder.task_agent_node", side_effect=mock_task),
        patch("backend.graph.builder.calendar_agent_node", side_effect=mock_calendar),
        patch("backend.graph.builder.focus_agent_node", side_effect=counting_focus),
        patch(
            "backend.graph.builder.verification_agent_node",
            AsyncMock(return_value=verification_return),
        ),
    ):
        graph = build_briefing_graph(mcp, llm=AsyncMock(), settings=settings)
        result = await graph.ainvoke(_base_state(trace_id=trace_id))

    assert focus_calls == 2
    assert result["status"] == "failure"
    assert result.get("failure_reason") == "max_retries_exceeded"
    assert result.get("dlq_events")
    assert result.get("critic_result") is None


@pytest.mark.asyncio
async def test_adversarial_exhausted_retries_route_to_dlq() -> None:
    trace_id = "j" * 32
    focus_calls = 0

    async def counting_focus(state: BriefingGraphState, llm: object) -> dict[str, Any]:
        nonlocal focus_calls
        focus_calls += 1
        return {
            "focus_result": AgentResultEnvelope(
                agent_id="focus",
                canonical_role="planner",
                status="success",
                result={"plan": {"summary": "Retry plan", "time_blocks": []}},
                metadata=_metadata(),
            ),
            "current_agent": "focus",
        }

    verification_return = {
        "verification_result": AgentResultEnvelope(
            agent_id="verification",
            canonical_role="verifier",
            status="success",
            result={
                "status": "verified",
                "flagged_claims": [],
                "verified_claims": ["Retry plan"],
                "confidence": 0.95,
            },
            metadata=_metadata(),
        ),
        "current_agent": "verification",
    }

    adversarial_return = {
        "adversarial_result": AgentResultEnvelope(
            agent_id="adversarial",
            canonical_role="adversarial",
            status="escalated",
            result={
                "challenges": [
                    {
                        "target": "Schedule density",
                        "concern": "No buffer between meetings",
                        "alternative": "Add 15-minute gaps",
                        "severity": "severe",
                    },
                ],
                "risk_level": "high",
                "recommended_action": "reject",
            },
            escalation=EscalationPayload(
                reason="adversarial_concerns",
                target_agent="focus",
                context=json.dumps({"challenges": []}),
                retry_allowed=True,
            ),
            metadata=_metadata(),
        ),
        "current_agent": "adversarial",
        "regeneration_constraints": json.dumps({"challenges": []}),
    }

    mcp = MCPClients(
        postgres=PostgresMCPClient(host="localhost", port=5443),
        calendar=CalendarMCPClient(host="localhost", port=5444),
    )
    settings = Settings(enable_consensus_workflow=True)

    async def mock_task(state: BriefingGraphState, postgres: object) -> dict[str, Any]:
        return {
            "task_result": AgentResultEnvelope(
                agent_id="task",
                canonical_role="doer",
                status="success",
                result={"tasks": []},
                metadata=_metadata(),
            ),
            "current_agent": "task",
        }

    async def mock_calendar(state: BriefingGraphState, calendar: object) -> dict[str, Any]:
        return {
            "calendar_result": AgentResultEnvelope(
                agent_id="calendar",
                canonical_role="tool_operator",
                status="success",
                result={"events": []},
                metadata=_metadata(),
            ),
            "current_agent": "calendar",
        }

    with (
        patch("backend.graph.builder.task_agent_node", side_effect=mock_task),
        patch("backend.graph.builder.calendar_agent_node", side_effect=mock_calendar),
        patch("backend.graph.builder.focus_agent_node", side_effect=counting_focus),
        patch(
            "backend.graph.builder.verification_agent_node",
            AsyncMock(return_value=verification_return),
        ),
        patch(
            "backend.graph.builder.adversarial_agent_node",
            AsyncMock(return_value=adversarial_return),
        ),
    ):
        graph = build_briefing_graph(mcp, llm=AsyncMock(), settings=settings)
        result = await graph.ainvoke(_base_state(trace_id=trace_id))

    assert focus_calls == 2
    assert result["status"] == "failure"
    assert result.get("failure_reason") == "max_retries_exceeded"
    assert result.get("dlq_events")
    assert result.get("critic_result") is None
