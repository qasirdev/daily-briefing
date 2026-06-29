"""Tests for Focus agent memory integration."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.focus.node import focus_agent_node
from backend.graph.state import BriefingGraphState
from backend.llm.models import LLMResponse
from backend.memory.audit import memory_audit_trail
from backend.memory.retrieval import AgentMemoryContext
from backend.memory.semantic import SemanticMemoryRecord, SemanticMemoryStore
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.security.spotlighting import EXTERNAL_CONTENT_OPEN, extract_spotlighted_content

TRACE_ID = "c" * 32


def _valid_focus_plan(**overrides: object) -> dict[str, object]:
    plan: dict[str, object] = {
        "summary": "Morning deep work on Q2 report before sprint review.",
        "time_blocks": [
            {
                "start": "09:00",
                "end": "11:00",
                "activity": "Complete Q2 report",
                "priority": "high",
                "type": "deep_work",
            },
        ],
        "top_priorities": [
            "Complete Q2 report",
            "Review sprint outcomes",
            "Prepare for team sync",
        ],
    }
    plan.update(overrides)
    return plan


def _metadata() -> ExecutionMetadata:
    return ExecutionMetadata(
        execution_ms=50,
        tokens_used=120,
        model_used="openai/gpt-4o-mini",
        prompt_version="v1.5.0",
        trace_id=TRACE_ID,
        data_classification="confidential",
    )


def _base_state() -> BriefingGraphState:
    return {
        "user_id": "user-1",
        "request_id": "req-1",
        "trace_id": TRACE_ID,
        "requested_at": datetime.now(UTC),
        "target_date": date.today(),
        "current_agent": "focus",
        "revision_count": 0,
        "total_tokens": 0,
        "working_memory_tokens": 0,
        "working_memory_limit": 16000,
        "working_memory_context": ["Earlier critic note"],
        "graph_started_at": 0.0,
        "status": "pending",
        "final_briefing": None,
        "consent_required": False,
        "consent_context": None,
        "consent_request": None,
        "dlq_events": [],
        "orchestrator_result": None,
        "task_result": AgentResultEnvelope(
            agent_id="task",
            canonical_role="doer",
            status="success",
            result={"tasks": [{"title": "Q2 report", "priority": "high"}]},
            metadata=_metadata(),
        ),
        "calendar_result": AgentResultEnvelope(
            agent_id="calendar",
            canonical_role="doer",
            status="success",
            result={"events": [{"summary": "Sprint Review", "start": "14:00"}]},
            metadata=_metadata(),
        ),
        "focus_result": None,
        "verification_result": None,
        "adversarial_result": None,
        "consensus_result": None,
        "critic_result": None,
    }


def _semantic_context() -> AgentMemoryContext:
    created_at = datetime.now(UTC)
    semantic_hit = SemanticMemoryRecord(
        id=uuid.uuid4(),
        user_id="user-1",
        content="Prior focus on Q2 report",
        source_type="briefing",
        source_id="brief-1",
        similarity=0.91,
        created_at=created_at,
    )
    return AgentMemoryContext(
        semantic=(semantic_hit,),
        procedural=(),
        episodic=(),
    )


@pytest.mark.asyncio
async def test_focus_includes_semantic_memory_in_llm_payload() -> None:
    memory_audit_trail.clear()

    mock_store = AsyncMock(spec=SemanticMemoryStore)
    mock_store.store = AsyncMock(return_value=uuid.uuid4())

    captured_messages: list[object] = []

    async def _generate(**kwargs: object) -> LLMResponse:
        captured_messages.append(kwargs.get("messages"))
        return LLMResponse(
            content=json.dumps(_valid_focus_plan(summary="Morning deep work on Q2 report")),
            tokens_used=150,
            model_used="openai/gpt-4o-mini",
            latency_ms=5,
        )

    mock_llm = AsyncMock()
    mock_llm.generate = _generate
    mock_llm.primary_model = "openai/gpt-4o-mini"

    with patch(
        "backend.agents.focus.node.retrieve_agent_memory",
        new=AsyncMock(return_value=_semantic_context()),
    ):
        update = await focus_agent_node(_base_state(), mock_llm, semantic_store=mock_store)

    assert update["focus_result"].status == "success"
    assert update["focus_result"].metadata.spotlighting_applied is True
    assert update["working_memory_tokens"] == 150
    assert "Morning deep work" in update["working_memory_context"][-1]
    mock_store.store.assert_awaited_once()

    messages = captured_messages[0]
    assert isinstance(messages, list)
    user_message = messages[-1]["content"]
    user_data = user_message.split("<user_data>\n", 1)[1].split("\n</user_data>", 1)[0]
    assert EXTERNAL_CONTENT_OPEN in user_data
    payload = json.loads(extract_spotlighted_content(user_data))
    assert payload["semantic_memory"][0]["content"] == "Prior focus on Q2 report"
    assert any(entry.memory_layer == "working" for entry in memory_audit_trail.entries)


@pytest.mark.asyncio
async def test_focus_continues_when_semantic_retrieval_fails() -> None:
    mock_store = AsyncMock(spec=SemanticMemoryStore)

    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(
            content=json.dumps(_valid_focus_plan(summary="Fallback plan")),
            tokens_used=80,
            model_used="openai/gpt-4o-mini",
            latency_ms=5,
        ),
    )
    mock_llm.primary_model = "openai/gpt-4o-mini"

    with patch(
        "backend.agents.focus.node.retrieve_agent_memory",
        new=AsyncMock(return_value=AgentMemoryContext(semantic=(), procedural=(), episodic=())),
    ):
        update = await focus_agent_node(_base_state(), mock_llm, semantic_store=mock_store)

    assert update["focus_result"].status == "success"
    assert update["working_memory_tokens"] == 80


@pytest.mark.asyncio
async def test_focus_unwraps_nested_plan_schema_from_llm() -> None:
    """LLM prompt schema wraps fields in a top-level `plan` key."""
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(
            content=json.dumps(
                {
                    "plan": _valid_focus_plan(),
                },
            ),
            tokens_used=150,
            model_used="openai/gpt-4o-mini",
            latency_ms=5,
        ),
    )
    mock_llm.primary_model = "openai/gpt-4o-mini"

    with patch(
        "backend.agents.focus.node.retrieve_agent_memory",
        new=AsyncMock(return_value=AgentMemoryContext(semantic=(), procedural=(), episodic=())),
    ):
        update = await focus_agent_node(_base_state(), mock_llm)

    plan = update["focus_result"].result["plan"]
    assert plan["summary"] == "Morning deep work on Q2 report before sprint review."
    assert len(plan["time_blocks"]) == 1
    assert "plan" not in plan


@pytest.mark.asyncio
async def test_focus_revision_loop_not_blocked_by_session_total_tokens() -> None:
    """Critic revisions accumulate total_tokens; focus must still invoke the LLM."""
    state = _base_state()
    state["total_tokens"] = 17_768
    state["revision_count"] = 2

    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(
            content=json.dumps(_valid_focus_plan(summary="Revised focus plan")),
            tokens_used=150,
            model_used="openai/gpt-4o-mini",
            latency_ms=5,
        ),
    )
    mock_llm.primary_model = "openai/gpt-4o-mini"

    with patch(
        "backend.agents.focus.node.retrieve_agent_memory",
        new=AsyncMock(return_value=AgentMemoryContext(semantic=(), procedural=(), episodic=())),
    ):
        update = await focus_agent_node(state, mock_llm)

    assert update["focus_result"].status == "success"
    mock_llm.generate.assert_awaited_once()
    assert update["total_tokens"] == 17_918


@pytest.mark.asyncio
async def test_focus_retries_when_first_llm_response_is_not_json() -> None:
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(
        side_effect=[
            LLMResponse(
                content="Sure, here is your plan for today with meetings and deep work.",
                tokens_used=120,
                model_used="deepseek/deepseek-v4-flash",
                latency_ms=5,
            ),
            LLMResponse(
                content=json.dumps(
                    {
                        "plan": _valid_focus_plan(
                            summary="Interview prep then deep work.",
                            time_blocks=[
                                {
                                    "start": "09:00",
                                    "end": "11:00",
                                    "activity": "Prepare for interview",
                                    "priority": "high",
                                    "type": "deep_work",
                                },
                            ],
                        ),
                    },
                ),
                tokens_used=140,
                model_used="deepseek/deepseek-v4-flash",
                latency_ms=5,
            ),
        ],
    )
    mock_llm.primary_model = "deepseek/deepseek-v4-flash"

    with patch(
        "backend.agents.focus.node.retrieve_agent_memory",
        new=AsyncMock(return_value=AgentMemoryContext(semantic=(), procedural=(), episodic=())),
    ):
        update = await focus_agent_node(_base_state(), mock_llm)

    assert update["focus_result"].status == "success"
    assert mock_llm.generate.await_count == 2
    plan = update["focus_result"].result["plan"]
    assert plan["summary"] == "Interview prep then deep work."
    assert update["total_tokens"] == 260


@pytest.mark.asyncio
async def test_focus_escalates_when_retry_still_invalid() -> None:
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(
        side_effect=[
            LLMResponse(
                content="Sure, here is your plan for today.",
                tokens_used=120,
                model_used="deepseek/deepseek-v4-flash",
                latency_ms=5,
            ),
            LLMResponse(
                content="Still not JSON, sorry.",
                tokens_used=140,
                model_used="deepseek/deepseek-v4-flash",
                latency_ms=5,
            ),
        ],
    )
    mock_llm.primary_model = "deepseek/deepseek-v4-flash"

    with patch(
        "backend.agents.focus.node.retrieve_agent_memory",
        new=AsyncMock(return_value=AgentMemoryContext(semantic=(), procedural=(), episodic=())),
    ):
        update = await focus_agent_node(_base_state(), mock_llm)

    envelope = update["focus_result"]
    assert envelope.status == "escalated"
    assert envelope.escalation is not None
    assert envelope.escalation.reason == "max_retries_exceeded"
    assert envelope.result is None


@pytest.mark.asyncio
async def test_focus_escalates_when_schema_invalid_after_retry() -> None:
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(
        side_effect=[
            LLMResponse(
                content=json.dumps({"summary": "Missing required fields"}),
                tokens_used=100,
                model_used="deepseek/deepseek-v4-flash",
                latency_ms=5,
            ),
            LLMResponse(
                content=json.dumps({"summary": "Still missing required fields"}),
                tokens_used=110,
                model_used="deepseek/deepseek-v4-flash",
                latency_ms=5,
            ),
        ],
    )
    mock_llm.primary_model = "deepseek/deepseek-v4-flash"

    with patch(
        "backend.agents.focus.node.retrieve_agent_memory",
        new=AsyncMock(return_value=AgentMemoryContext(semantic=(), procedural=(), episodic=())),
    ):
        update = await focus_agent_node(_base_state(), mock_llm)

    envelope = update["focus_result"]
    assert envelope.status == "escalated"
    assert envelope.escalation is not None
    assert envelope.escalation.reason == "max_retries_exceeded"
    assert envelope.result is None
