"""Tests for working memory manager."""

from typing import cast

from backend.graph.state import BriefingGraphState
from backend.memory.working import WorkingMemoryManager
from backend.settings import Settings


def _state(**overrides: object) -> BriefingGraphState:
    base: BriefingGraphState = {
        "user_id": "user-1",
        "request_id": "req-1",
        "trace_id": "a" * 32,
        "current_agent": "orchestrator",
        "total_tokens": 0,
        "working_memory_tokens": 0,
        "working_memory_limit": 1000,
        "working_memory_context": [],
    }
    if overrides:
        merged = cast(BriefingGraphState, {**base, **overrides})
        return merged
    return base


def test_initialize_state_sets_defaults() -> None:
    manager = WorkingMemoryManager(Settings(working_memory_token_limit=8000))
    update = manager.initialize_state(_state())
    assert update["working_memory_limit"] == 8000
    assert update["working_memory_tokens"] == 0
    assert update["working_memory_context"] == []


def test_record_agent_turn_accumulates_tokens_and_snippets() -> None:
    manager = WorkingMemoryManager(Settings(working_memory_max_snippets=2))
    first = manager.record_agent_turn(
        _state(),
        agent_id="focus",
        tokens_used=100,
        context_snippet="Generated focus plan",
    )
    second = manager.record_agent_turn(
        cast(BriefingGraphState, {**_state(), **first}),
        agent_id="critic",
        tokens_used=50,
        context_snippet="Critic approved plan",
    )
    assert second["working_memory_tokens"] == 150
    assert second["working_memory_context"] == ["Generated focus plan", "Critic approved plan"]


def test_record_agent_turn_trims_snippets_to_max() -> None:
    manager = WorkingMemoryManager(Settings(working_memory_max_snippets=2))
    state = _state()
    turn_a = manager.record_agent_turn(state, agent_id="a", tokens_used=1, context_snippet="one")
    state = cast(BriefingGraphState, {**state, **turn_a})
    turn_b = manager.record_agent_turn(state, agent_id="b", tokens_used=1, context_snippet="two")
    state = cast(BriefingGraphState, {**state, **turn_b})
    turn_c = manager.record_agent_turn(state, agent_id="c", tokens_used=1, context_snippet="three")
    state = cast(BriefingGraphState, {**state, **turn_c})
    assert state["working_memory_context"] == ["two", "three"]


def test_exceeds_budget_when_over_limit() -> None:
    manager = WorkingMemoryManager(Settings(working_memory_token_limit=100))
    state = _state(working_memory_tokens=150, working_memory_limit=100)
    assert manager.exceeds_budget(state) is True


def test_snapshot_reports_utilization() -> None:
    manager = WorkingMemoryManager(Settings(working_memory_token_limit=200))
    snapshot = manager.snapshot(_state(working_memory_tokens=50, working_memory_limit=200))
    assert snapshot.utilization == 0.25
    assert snapshot.budget_remaining == 150
