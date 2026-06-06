"""Integration tests for Week 8 production optimization."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from backend.memory.agentic_rag import decide_retrieval
from backend.memory.context_compression import compress_memory_payload
from backend.memory.retrieval import get_retrieval_decision_for_state
from backend.memory.source_validation import validate_source_provenance
from backend.observability.deployment_gates import check_deployment_gates
from backend.security.enumeration_detector import EnumerationDetector
from backend.settings import Settings


def test_agentic_rag_to_compression_pipeline() -> None:
    decision = decide_retrieval(
        user_id="user-1",
        agent_id="focus",
        query_text="sprint planning",
        task_count=3,
        has_prior_briefings=True,
    )
    assert decision.kind == "full"
    payload: dict[str, list[dict[str, Any]]] = {
        "semantic_memory": [{"content": "x" * 600, "similarity": 0.8}],
        "procedural_skills": [{"name": "y" * 600, "skill_key": "k1", "steps": [], "tools": []}],
        "episodic_lessons": [],
    }
    compressed, saved = compress_memory_payload(payload, max_chars=500)
    assert saved > 0 or len(compressed["semantic_memory"]) <= 1


def test_source_validation_before_compression() -> None:
    import uuid
    from datetime import UTC, datetime

    from backend.memory.semantic import SemanticMemoryRecord

    records = [
        SemanticMemoryRecord(
            id=uuid.uuid4(),
            user_id="u",
            content="trusted",
            source_type="briefing",
            source_trust="internal",
            similarity=0.9,
            created_at=datetime.now(UTC),
        ),
        SemanticMemoryRecord(
            id=uuid.uuid4(),
            user_id="u",
            content="untrusted",
            source_type="briefing",
            source_trust="untrusted",
            similarity=0.9,
            created_at=datetime.now(UTC),
        ),
    ]
    validated, dropped = validate_source_provenance(records)
    assert len(validated) == 1
    assert dropped == 1


def test_retrieval_decision_exposed_for_observability() -> None:
    decision = get_retrieval_decision_for_state(
        user_id="user-1",
        agent_id="focus",
        query_text="plan",
        task_count=1,
    )
    assert decision.reason


def test_enumeration_and_gates_coexist() -> None:
    detector = EnumerationDetector(Settings(enumeration_probe_threshold=100))
    detector.record_probe(probe_type="consent_list", subject="user-x")
    report = check_deployment_gates(Settings(enable_agentic_rag=True))
    assert report.gates


@pytest.mark.asyncio
async def test_reasoning_feedback_integration_path() -> None:
    from backend.feedback.reasoning import store_reasoning_feedback
    from backend.schemas.reasoning_feedback import ReasoningFeedbackRequest

    mock_store = AsyncMock()
    mock_store.store_lesson = AsyncMock(return_value="id-1")
    body = ReasoningFeedbackRequest(
        user_id="user-1",
        briefing_id="b1",
        trace_id="d" * 32,
        agent_id="focus",
        rating="correct",
    )
    with patch("backend.feedback.reasoning._default_store", mock_store):
        lesson_id = await store_reasoning_feedback(body, store=mock_store)
    assert lesson_id == "id-1"
