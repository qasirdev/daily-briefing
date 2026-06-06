"""Week 2 Day 5 memory integration scenarios."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.focus.node import focus_agent_node
from backend.graph.state import BriefingGraphState
from backend.llm.models import LLMResponse
from backend.memory.audit import memory_audit_trail
from backend.memory.consolidation import consolidate_semantic_memory
from backend.memory.embeddings import deterministic_embedding, embed_text
from backend.memory.retrieval import (
    build_focus_retrieval_query,
    format_semantic_context,
    retrieve_semantic_context,
)
from backend.memory.semantic import SemanticMemoryRecord, SemanticMemoryStore
from backend.memory.working import WorkingMemoryManager
from backend.observability.metrics import (
    MEMORY_READS_TOTAL,
    SEMANTIC_SEARCH_DURATION,
    WORKING_MEMORY_UTILIZATION,
)
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.settings import Settings

TRACE_ID = "d" * 32


def _metadata() -> ExecutionMetadata:
    return ExecutionMetadata(
        execution_ms=50,
        tokens_used=100,
        model_used="openai/gpt-4o-mini",
        prompt_version="v1.5.0",
        trace_id=TRACE_ID,
        data_classification="confidential",
    )


def _focus_state(**overrides: object) -> BriefingGraphState:
    state: BriefingGraphState = {
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
        "working_memory_context": [],
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
            result={"tasks": [{"title": "Deploy hotfix"}]},
            metadata=_metadata(),
        ),
        "calendar_result": AgentResultEnvelope(
            agent_id="calendar",
            canonical_role="doer",
            status="success",
            result={"events": [{"summary": "Team sync"}]},
            metadata=_metadata(),
        ),
        "focus_result": None,
        "verification_result": None,
        "adversarial_result": None,
        "consensus_result": None,
        "critic_result": None,
    }
    state.update(overrides)  # type: ignore[typeddict-item]
    return state


@pytest.mark.asyncio
async def test_integration_01_working_memory_seeded_at_graph_start() -> None:
    manager = WorkingMemoryManager(Settings(working_memory_token_limit=8000))
    state = _focus_state(total_tokens=250)
    state.pop("working_memory_tokens", None)
    update = manager.initialize_state(state)
    assert update["working_memory_tokens"] == 250
    assert update["working_memory_limit"] == 8000


@pytest.mark.asyncio
async def test_integration_02_cross_layer_working_to_semantic() -> None:
    memory_audit_trail.clear()
    mock_store = AsyncMock(spec=SemanticMemoryStore)
    mock_store.search_similar = AsyncMock(return_value=[])

    await retrieve_semantic_context(
        user_id="user-1",
        query_text="",
        trace_id=TRACE_ID,
        agent_id="focus",
        store=mock_store,
        working_context=["Deploy hotfix", "Team sync"],
    )

    called_embedding = mock_store.search_similar.await_args.kwargs["embedding"]
    assert len(called_embedding) == Settings().semantic_memory_embedding_dim


@pytest.mark.asyncio
async def test_integration_03_semantic_retrieval_skips_without_user_id() -> None:
    memory_audit_trail.clear()
    mock_store = AsyncMock(spec=SemanticMemoryStore)
    records = await retrieve_semantic_context(
        user_id="",
        query_text="daily briefing",
        trace_id=TRACE_ID,
        agent_id="focus",
        store=mock_store,
    )
    assert records == []
    mock_store.search_similar.assert_not_called()


@pytest.mark.asyncio
async def test_integration_04_semantic_disabled_returns_empty() -> None:
    mock_store = AsyncMock(spec=SemanticMemoryStore)
    records = await retrieve_semantic_context(
        user_id="user-1",
        query_text="standup",
        trace_id=TRACE_ID,
        agent_id="focus",
        store=mock_store,
        settings=Settings(enable_semantic_memory_retrieval=False),
    )
    assert records == []
    mock_store.search_similar.assert_not_called()


def test_integration_05_format_semantic_context_shape() -> None:
    record = SemanticMemoryRecord(
        id=uuid.uuid4(),
        user_id="user-1",
        content="Prior plan",
        source_type="briefing",
        source_id="b-1",
        similarity=0.87654321,
        created_at=datetime.now(UTC),
    )
    payload = format_semantic_context([record])
    assert payload == [
        {
            "content": "Prior plan",
            "source_type": "briefing",
            "source_id": "b-1",
            "similarity": 0.8765,
        },
    ]


def test_integration_06_build_query_from_tasks_events_and_working() -> None:
    query = build_focus_retrieval_query(
        tasks=[{"title": "Deploy hotfix"}],
        events=[{"summary": "Team sync"}],
        working_context=["Revision requested"],
    )
    assert "Deploy hotfix" in query
    assert "Team sync" in query
    assert "Revision requested" in query


@pytest.mark.asyncio
async def test_integration_07_audit_trail_captures_semantic_reads() -> None:
    memory_audit_trail.clear()
    mock_store = AsyncMock(spec=SemanticMemoryStore)
    mock_store.search_similar = AsyncMock(return_value=[])

    await retrieve_semantic_context(
        user_id="user-1",
        query_text="hotfix planning",
        trace_id=TRACE_ID,
        agent_id="focus",
        request_id="req-7",
        store=mock_store,
    )

    assert len(memory_audit_trail.entries) == 1
    assert memory_audit_trail.entries[0].memory_layer == "semantic"
    assert memory_audit_trail.entries[0].request_id == "req-7"


@pytest.mark.asyncio
async def test_integration_08_working_memory_updates_after_focus_turn() -> None:
    mock_store = AsyncMock(spec=SemanticMemoryStore)
    mock_store.search_similar = AsyncMock(return_value=[])
    mock_store.store = AsyncMock(return_value=uuid.uuid4())

    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(
            content=json.dumps({"summary": "Plan A", "time_blocks": []}),
            tokens_used=200,
            model_used="openai/gpt-4o-mini",
            latency_ms=5,
        ),
    )
    mock_llm.primary_model = "openai/gpt-4o-mini"

    update = await focus_agent_node(_focus_state(), mock_llm, semantic_store=mock_store)
    assert update["working_memory_tokens"] == 200
    assert update["working_memory_context"][-1] == "Plan A"


@pytest.mark.asyncio
async def test_integration_09_focus_survives_semantic_store_failure() -> None:
    mock_store = AsyncMock(spec=SemanticMemoryStore)
    mock_store.search_similar = AsyncMock(side_effect=OSError("connection reset"))

    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(
        return_value=LLMResponse(
            content=json.dumps({"summary": "Resilient plan", "time_blocks": []}),
            tokens_used=90,
            model_used="openai/gpt-4o-mini",
            latency_ms=5,
        ),
    )
    mock_llm.primary_model = "openai/gpt-4o-mini"

    update = await focus_agent_node(_focus_state(), mock_llm, semantic_store=mock_store)
    assert update["focus_result"].status == "success"


@pytest.mark.asyncio
async def test_integration_10_consolidation_prunes_stale_semantic_rows() -> None:
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 3
    mock_session.execute = AsyncMock(return_value=mock_result)

    class _SessionContext:
        async def __aenter__(self) -> AsyncMock:
            return mock_session

        async def __aexit__(self, *args: object) -> None:
            return None

    with patch("backend.memory.consolidation.session_scope", return_value=_SessionContext()):
        consolidated = await consolidate_semantic_memory(user_id="user-1", max_age_days=30)

    assert consolidated == 3


def test_integration_11_embedding_pipeline_is_deterministic() -> None:
    first = embed_text("Deploy hotfix", Settings(semantic_memory_embedding_dim=16))
    second = embed_text("Deploy hotfix", Settings(semantic_memory_embedding_dim=16))
    assert first == second
    assert len(first) == 16


@pytest.mark.asyncio
async def test_integration_12_metrics_recorded_on_semantic_search() -> None:
    memory_audit_trail.clear()
    agent_id = "focus-integration-12"
    created_at = datetime.now(UTC)
    mock_records = [
        SemanticMemoryRecord(
            id=uuid.uuid4(),
            user_id="user-1",
            content="Cached context",
            source_type="briefing",
            source_id="b-12",
            similarity=0.8,
            created_at=created_at,
        ),
    ]
    mock_store = AsyncMock(spec=SemanticMemoryStore)
    mock_store.search_similar = AsyncMock(return_value=mock_records)

    initial_reads = MEMORY_READS_TOTAL.labels(
        memory_layer="semantic",
        agent_id=agent_id,
    )._value.get()

    with patch("backend.memory.retrieval.record_semantic_search_duration") as mock_duration:
        await retrieve_semantic_context(
            user_id="user-1",
            query_text="metrics check",
            trace_id=TRACE_ID,
            agent_id=agent_id,
            store=mock_store,
        )
        mock_duration.assert_called_once()

    final_reads = MEMORY_READS_TOTAL.labels(
        memory_layer="semantic",
        agent_id=agent_id,
    )._value.get()
    assert final_reads == initial_reads + 1


def test_integration_13_working_memory_utilization_gauge_updates() -> None:
    manager = WorkingMemoryManager(Settings(working_memory_token_limit=1000))
    state = _focus_state(working_memory_tokens=0, working_memory_limit=1000)
    manager.record_agent_turn(state, agent_id="focus", tokens_used=500)
    utilization = WORKING_MEMORY_UTILIZATION._value.get()
    assert utilization == pytest.approx(0.5)


def test_integration_14_semantic_search_histogram_observes_latency() -> None:
    from backend.metrics import record_semantic_search_duration

    agent_id = "focus-integration-14"
    before = SEMANTIC_SEARCH_DURATION.labels(agent_id=agent_id)._sum.get()
    record_semantic_search_duration(duration_ms=5.0, agent_id=agent_id)
    after = SEMANTIC_SEARCH_DURATION.labels(agent_id=agent_id)._sum.get()
    assert after > before


def test_integration_15_deterministic_embedding_unit_norm() -> None:
    vector = deterministic_embedding("memory integration", dimensions=32)
    norm = sum(value * value for value in vector) ** 0.5
    assert norm == pytest.approx(1.0, rel=1e-5)
