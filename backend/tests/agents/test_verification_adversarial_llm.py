"""Tests for verification and adversarial LLM nodes (Week 2 Day 2)."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock

import pytest

from backend.agents.adversarial.node import adversarial_agent_node
from backend.agents.verification.node import verification_agent_node
from backend.graph.state import BriefingGraphState
from backend.llm.models import LLMResponse
from backend.llm.prompt_cache import build_llm_messages, openai_cache_eligible
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata

TRACE_ID = "d" * 32


def _metadata() -> ExecutionMetadata:
    return ExecutionMetadata(
        execution_ms=50,
        tokens_used=10,
        model_used="openai/gpt-4o-mini",
        prompt_version="v1.1.0",
        trace_id=TRACE_ID,
        data_classification="internal",
    )


def _base_state() -> BriefingGraphState:
    return {
        "user_id": "user-1",
        "request_id": "req-1",
        "trace_id": TRACE_ID,
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
        "focus_result": AgentResultEnvelope(
            agent_id="focus",
            canonical_role="planner",
            status="success",
            result={
                "plan": {
                    "summary": "Morning deep work",
                    "time_blocks": [{"start": "09:00", "end": "11:00", "activity": "Q2 report"}],
                },
            },
            metadata=_metadata(),
        ),
        "verification_result": None,
        "adversarial_result": None,
        "consensus_result": None,
        "critic_result": None,
    }


@pytest.mark.asyncio
async def test_verification_node_uses_llm_with_cached_prompt() -> None:
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value=LLMResponse(
            content=json.dumps(
                {
                    "status": "verified",
                    "verified_claims": ["Plan aligns with MCP data"],
                    "flagged_claims": [],
                    "confidence": 1.0,
                },
            ),
            model_used="openai/gpt-4o-mini",
            tokens_used=120,
            latency_ms=5,
        ),
    )

    result = await verification_agent_node(_base_state(), llm)
    envelope = result["verification_result"]
    assert isinstance(envelope, AgentResultEnvelope)
    assert envelope.status == "success"
    assert envelope.result is not None
    assert envelope.result["status"] == "verified"
    assert envelope.metadata.tokens_used == 120
    assert envelope.metadata.prompt_version == "v2.0.0"

    call_kwargs = llm.generate.await_args.kwargs
    messages = call_kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert call_kwargs["agent_id"] == "verification"


@pytest.mark.asyncio
async def test_verification_node_falls_back_on_invalid_llm_json() -> None:
    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value=LLMResponse(
            content="not json",
            model_used="openai/gpt-4o-mini",
            tokens_used=10,
            latency_ms=1,
        ),
    )

    result = await verification_agent_node(_base_state(), llm)
    envelope = result["verification_result"]
    assert isinstance(envelope, AgentResultEnvelope)
    assert envelope.result is not None
    assert "status" in envelope.result


@pytest.mark.asyncio
async def test_adversarial_node_uses_llm_with_cached_prompt() -> None:
    state = _base_state()
    state["verification_result"] = AgentResultEnvelope(
        agent_id="verification",
        canonical_role="verifier",
        status="success",
        result={
            "status": "verified",
            "verified_claims": ["ok"],
            "flagged_claims": [],
            "confidence": 1.0,
        },
        metadata=_metadata(),
    )

    llm = AsyncMock()
    llm.generate = AsyncMock(
        return_value=LLMResponse(
            content=json.dumps(
                {
                    "challenges": [],
                    "risk_level": "low",
                    "recommended_action": "approve",
                },
            ),
            model_used="openai/gpt-4o-mini",
            tokens_used=95,
            latency_ms=4,
        ),
    )

    result = await adversarial_agent_node(state, llm)
    envelope = result["adversarial_result"]
    assert isinstance(envelope, AgentResultEnvelope)
    assert envelope.result is not None
    assert envelope.result["recommended_action"] == "approve"
    assert envelope.metadata.tokens_used == 95

    call_kwargs = llm.generate.await_args.kwargs
    assert call_kwargs["agent_id"] == "adversarial"


@pytest.mark.parametrize(
    "agent_id",
    ["focus", "verification", "adversarial"],
)
def test_cached_agents_openai_cache_eligible(agent_id: str) -> None:
    assert openai_cache_eligible(agent_id)


def test_verification_messages_use_stable_system_prefix() -> None:
    messages = build_llm_messages(
        "verification",
        "dynamic payload",
        model="openai/gpt-4o-mini",
    )
    system_content = messages[0]["content"]
    assert isinstance(system_content, str)
    assert len(system_content) >= 4096
