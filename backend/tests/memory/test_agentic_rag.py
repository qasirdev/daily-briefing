"""Tests for agentic RAG decision engine."""

from __future__ import annotations

from backend.memory.agentic_rag import decide_retrieval, refine_query, should_retry_retrieval
from backend.settings import Settings


def test_anonymous_user_skips_retrieval() -> None:
    decision = decide_retrieval(user_id="", agent_id="focus", query_text="plan")
    assert decision.kind == "skip"
    assert decision.layers == frozenset()


def test_legacy_mode_retrieves_all_layers() -> None:
    decision = decide_retrieval(
        user_id="user-1",
        agent_id="focus",
        query_text="standup",
        settings=Settings(enable_agentic_rag=False),
    )
    assert decision.kind == "full"
    assert decision.layers == frozenset({"semantic", "procedural", "episodic"})


def test_first_session_skips_semantic() -> None:
    decision = decide_retrieval(
        user_id="user-1",
        agent_id="focus",
        query_text="daily plan",
        task_count=1,
        has_prior_briefings=False,
    )
    assert "semantic" not in decision.layers
    assert "procedural" in decision.layers


def test_rich_context_full_retrieval() -> None:
    decision = decide_retrieval(
        user_id="user-1",
        agent_id="focus",
        query_text="Q2 report",
        task_count=2,
        event_count=2,
        working_context_count=2,
        has_prior_briefings=True,
    )
    assert decision.kind == "full"
    assert decision.layers == frozenset({"semantic", "procedural", "episodic"})


def test_empty_context_procedural_only() -> None:
    decision = decide_retrieval(
        user_id="user-1",
        agent_id="focus",
        query_text="",
    )
    assert decision.kind == "partial"
    assert decision.layers == frozenset({"procedural"})


def test_refine_query_broadens_on_miss() -> None:
    query, pass_num, retry = refine_query(
        base_query="standup",
        semantic_hit_count=0,
        refinement_pass=0,
    )
    assert retry is True
    assert pass_num == 1
    assert "historical" in query


def test_refine_query_stops_after_hits() -> None:
    query, pass_num, retry = refine_query(
        base_query="standup",
        semantic_hit_count=3,
        refinement_pass=0,
    )
    assert retry is False
    assert query == "standup"
    assert pass_num == 0


def test_should_retry_when_semantic_empty() -> None:
    decision = decide_retrieval(
        user_id="user-1",
        agent_id="focus",
        query_text="plan",
        has_prior_briefings=True,
    )
    assert should_retry_retrieval(
        decision=decision,
        semantic_hit_count=0,
        refinement_pass=0,
    )


def test_should_not_retry_without_semantic_layer() -> None:
    decision = decide_retrieval(
        user_id="user-1",
        agent_id="focus",
        query_text="",
    )
    assert not should_retry_retrieval(
        decision=decision,
        semantic_hit_count=0,
        refinement_pass=0,
    )
