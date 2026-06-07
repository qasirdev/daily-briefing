"""Token budget circuit breaker tests."""

from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.security.token_budget import (
    AGENT_TOKEN_BUDGETS,
    evaluate_token_budget,
    has_presentable_results,
    is_session_token_exceeded,
    session_token_hard_limit,
)


def _envelope(*, agent_id: str, tokens: int) -> AgentResultEnvelope:
    return AgentResultEnvelope(
        agent_id=agent_id,
        canonical_role="doer",
        status="success",
        result={"ok": True},
        metadata=ExecutionMetadata(
            execution_ms=1,
            tokens_used=tokens,
            model_used="none",
            prompt_version="v1.5.0",
            trace_id="f" * 32,
            data_classification="internal",
        ),
    )


def test_within_budget_does_not_break() -> None:
    state: BriefingGraphState = {
        "focus_result": _envelope(agent_id="focus", tokens=AGENT_TOKEN_BUDGETS["focus"]),
    }
    assert evaluate_token_budget(state) == "none"


def test_exceeding_hard_limit_triggers_break() -> None:
    over = AGENT_TOKEN_BUDGETS["focus"] * 2 + 1
    state: BriefingGraphState = {
        "focus_result": _envelope(agent_id="focus", tokens=over),
    }
    assert evaluate_token_budget(state) == "token_budget_exceeded"


def test_session_limit_allows_revision_loop_totals() -> None:
    assert session_token_hard_limit(configured_max=16_000) >= 90_000
    state: BriefingGraphState = {
        "total_tokens": 36_257,
        "focus_result": _envelope(agent_id="focus", tokens=18_146),
    }
    assert not is_session_token_exceeded(state, configured_max=16_000)


def test_has_presentable_results_detects_successful_focus() -> None:
    state: BriefingGraphState = {
        "focus_result": _envelope(agent_id="focus", tokens=100),
    }
    assert has_presentable_results(state) is True
