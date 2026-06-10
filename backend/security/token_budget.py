"""Per-agent token budget enforcement for LangGraph circuit breaking."""

from __future__ import annotations

from typing import Literal

from backend.graph.state import BriefingGraphState
from backend.metrics import set_token_budget_utilization
from backend.schemas.envelope import AgentResultEnvelope

AGENT_TOKEN_BUDGETS: dict[str, int] = {
    "task": 3_000,
    "calendar": 3_000,
    "focus": 10_000,
    "verification": 4_000,
    "adversarial": 4_000,
    "critic": 5_000,
}

HARD_LIMIT_MULTIPLIER = 2
MAX_CRITIC_REVISION_CYCLES = 2

CircuitBreakReason = Literal["token_budget_exceeded", "graph_timeout", "none"]

_LLM_AGENT_IDS = ("focus", "critic", "verification", "adversarial")

_AGENT_RESULT_KEYS: tuple[tuple[str, str], ...] = (
    ("task", "task_result"),
    ("calendar", "calendar_result"),
    ("focus", "focus_result"),
    ("verification", "verification_result"),
    ("adversarial", "adversarial_result"),
    ("critic", "critic_result"),
)


def _agent_tokens_used(state: BriefingGraphState, agent_id: str) -> int:
    for name, key in _AGENT_RESULT_KEYS:
        if name != agent_id:
            continue
        envelope = state.get(key)
        if isinstance(envelope, AgentResultEnvelope):
            return envelope.metadata.tokens_used
    return 0


def session_token_hard_limit(
    *,
    max_revision_cycles: int = MAX_CRITIC_REVISION_CYCLES,
    configured_max: int | None = None,
) -> int:
    """Session ceiling sized for focus + critic through max revision cycles."""
    focus_runs = max_revision_cycles + 1
    computed = sum(
        AGENT_TOKEN_BUDGETS[agent_id] * HARD_LIMIT_MULTIPLIER * focus_runs
        for agent_id in _LLM_AGENT_IDS
        if agent_id in AGENT_TOKEN_BUDGETS
    )
    if configured_max is None:
        return computed
    return max(computed, configured_max * HARD_LIMIT_MULTIPLIER)


def is_session_token_exceeded(
    state: BriefingGraphState,
    *,
    configured_max: int | None = None,
) -> bool:
    """Return True when cumulative session tokens exceed the revision-aware ceiling."""
    total_tokens = state.get("total_tokens", 0)
    return total_tokens > session_token_hard_limit(configured_max=configured_max)


def has_presentable_results(state: BriefingGraphState) -> bool:
    """Return True when at least one briefing component completed successfully."""
    for key in ("task_result", "calendar_result", "focus_result"):
        envelope = state.get(key)
        if isinstance(envelope, AgentResultEnvelope) and envelope.status == "success":
            return True
    return False


def evaluate_token_budget(state: BriefingGraphState) -> CircuitBreakReason:
    """Return the circuit-break reason when any agent exceeds 2x its budget."""
    for agent_id, budget in AGENT_TOKEN_BUDGETS.items():
        used = _agent_tokens_used(state, agent_id)
        hard_limit = budget * HARD_LIMIT_MULTIPLIER
        utilization = used / budget if budget else 0.0
        set_token_budget_utilization(agent_id=agent_id, utilization=utilization)
        if used > hard_limit:
            return "token_budget_exceeded"
    return "none"


def exceeded_agent_id(state: BriefingGraphState) -> str | None:
    """Return the first agent that exceeded its hard token limit."""
    for agent_id, budget in AGENT_TOKEN_BUDGETS.items():
        used = _agent_tokens_used(state, agent_id)
        if used > budget * HARD_LIMIT_MULTIPLIER:
            return agent_id
    return None
