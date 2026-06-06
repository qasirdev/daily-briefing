"""Tests for Day 4 AgentOps metrics and orchestrator distillation."""

from __future__ import annotations

from typing import Literal, cast
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.consensus.node import consensus_evaluator_node
from backend.agents.orchestrator.node import orchestrator_present_node
from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.tests.memory.test_quarantine import _session_context

TRACE_ID = "a" * 32


def _envelope(
    *,
    status: Literal["success", "failure", "escalated"] = "success",
    result: dict[str, object] | None = None,
) -> AgentResultEnvelope:
    return AgentResultEnvelope(
        agent_id="task",
        canonical_role="doer",
        status=status,
        result=result or {},
        metadata=ExecutionMetadata(
            execution_ms=1,
            tokens_used=10,
            model_used="test",
            prompt_version="v1.5.0",
            trace_id=TRACE_ID,
            data_classification="internal",
        ),
    )


@pytest.mark.asyncio
async def test_consensus_records_disagreement_metric() -> None:
    state = {
        "verification_result": _envelope(
            status="escalated",
            result={"flagged_claims": [{"severity": "critical"}]},
        ),
        "adversarial_result": _envelope(
            result={"challenges": [{"severity": "severe"}]},
        ),
    }
    with patch("backend.agents.consensus.node.record_consensus_disagreement") as mock_metric:
        update = await consensus_evaluator_node(cast(BriefingGraphState, state))

    assert update["consensus_result"]["agreement_level"] == "major_disagreement"
    mock_metric.assert_called_once_with(agreement_level="major_disagreement")


@pytest.mark.asyncio
async def test_consensus_skips_metric_on_agreement() -> None:
    state = {
        "verification_result": _envelope(result={"flagged_claims": []}),
        "adversarial_result": _envelope(result={"challenges": []}),
    }
    with patch("backend.agents.consensus.node.record_consensus_disagreement") as mock_metric:
        update = await consensus_evaluator_node(cast(BriefingGraphState, state))

    assert update["consensus_result"]["agreement_level"] == "agreement"
    mock_metric.assert_not_called()


@pytest.mark.asyncio
async def test_orchestrator_distills_working_memory_after_present() -> None:
    state = {
        "trace_id": TRACE_ID,
        "request_id": "req-123",
        "user_id": "user-1",
        "total_tokens": 100,
        "working_memory_context": ["Focus on Q2 planning", "Review sprint board"],
        "task_result": _envelope(result={"tasks": [{"title": "Write report", "priority": "high"}]}),
        "calendar_result": None,
        "focus_result": _envelope(
            result={"plan": {"summary": "Deep work on Q2 report", "time_blocks": []}},
        ),
        "critic_result": None,
    }
    with patch(
        "backend.agents.orchestrator.node.distill_working_to_episodic",
        new=AsyncMock(return_value="lesson-id"),
    ) as mock_distill:
        await orchestrator_present_node(cast(BriefingGraphState, state))

    mock_distill.assert_awaited_once_with(
        user_id="user-1",
        session_id="req-123",
        working_context=["Focus on Q2 planning", "Review sprint board"],
    )


@pytest.mark.asyncio
async def test_episodic_store_rejects_fully_redacted_summary() -> None:
    from backend.memory.episodic import EpisodicMemoryStore

    store = EpisodicMemoryStore()
    mock_session = AsyncMock()

    session_ctx = _session_context(mock_session)()
    with patch("backend.memory.episodic.session_scope", return_value=session_ctx):
        with pytest.raises(ValueError, match="empty after privilege sanitization"):
            await store.store_lesson(
                user_id="user-1",
                session_id="session-1",
                lesson_type="session_summary",
                summary="api_key=secret-only-content",
            )
