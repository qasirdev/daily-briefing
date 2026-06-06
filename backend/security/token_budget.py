"""Per-agent token budget enforcement for LangGraph circuit breaking."""

from __future__ import annotations

from typing import Literal

from backend.graph.state import BriefingGraphState
from backend.metrics import set_token_budget_utilization
from backend.schemas.envelope import AgentResultEnvelope

AGENT_TOKEN_BUDGETS: dict[str, int] = {
    "task": 3_000,
    "calendar": 3_000,
    "focus": 6_000,
    "verification": 4_000,
    "adversarial": 4_000,
    "critic": 5_000,
}

HARD_LIMIT_MULTIPLIER = 2

CircuitBreakReason = Literal["token_budget_exceeded", "graph_timeout", "none"]

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
