"""Ephemeral working memory for LangGraph session state (CoALA layer 1)."""

from __future__ import annotations

from dataclasses import dataclass

from backend.graph.state import BriefingGraphState
from backend.metrics import set_token_budget_utilization
from backend.settings import Settings, get_settings


@dataclass(frozen=True)
class WorkingMemorySnapshot:
    """Session-scoped working memory snapshot."""

    request_id: str
    trace_id: str
    active_agent: str
    tokens_used: int
    token_limit: int
    context_snippets: tuple[str, ...]

    @property
    def utilization(self) -> float:
        if self.token_limit <= 0:
            return 0.0
        return self.tokens_used / self.token_limit

    @property
    def budget_remaining(self) -> int:
        return max(self.token_limit - self.tokens_used, 0)


class WorkingMemoryManager:
    """Manage session-scoped working memory and token budget tracking."""

    def __init__(self, settings: Settings | None = None) -> None:
        resolved = settings or get_settings()
        self._token_limit = resolved.working_memory_token_limit
        self._max_snippets = resolved.working_memory_max_snippets

    def initialize_state(self, state: BriefingGraphState) -> dict[str, object]:
        """Seed working memory fields at graph start."""
        return {
            "working_memory_tokens": state.get(
                "working_memory_tokens",
                state.get("total_tokens", 0),
            ),
            "working_memory_limit": self._token_limit,
            "working_memory_context": list(state.get("working_memory_context", ())),
        }

    def snapshot(self, state: BriefingGraphState) -> WorkingMemorySnapshot:
        """Capture the current working memory view."""
        snippets = state.get("working_memory_context", [])
        normalized = tuple(str(item) for item in snippets) if isinstance(snippets, list) else ()
        return WorkingMemorySnapshot(
            request_id=state.get("request_id", ""),
            trace_id=state.get("trace_id", "0" * 32),
            active_agent=state.get("current_agent", ""),
            tokens_used=int(state.get("working_memory_tokens", state.get("total_tokens", 0))),
            token_limit=int(state.get("working_memory_limit", self._token_limit)),
            context_snippets=normalized[: self._max_snippets],
        )

    def record_agent_turn(
        self,
        state: BriefingGraphState,
        *,
        agent_id: str,
        tokens_used: int,
        context_snippet: str | None = None,
    ) -> dict[str, object]:
        """Update working memory after an agent completes."""
        current_tokens = int(state.get("working_memory_tokens", state.get("total_tokens", 0)))
        updated_tokens = current_tokens + max(tokens_used, 0)
        limit = int(state.get("working_memory_limit", self._token_limit))
        snippets = list(state.get("working_memory_context", []))
        if context_snippet:
            snippets.append(context_snippet.strip()[:500])
            snippets = snippets[-self._max_snippets :]

        utilization = updated_tokens / limit if limit else 0.0
        set_token_budget_utilization(agent_id=agent_id, utilization=utilization)

        return {
            "working_memory_tokens": updated_tokens,
            "working_memory_limit": limit,
            "working_memory_context": snippets,
            "current_agent": agent_id,
        }

    def exceeds_budget(self, state: BriefingGraphState) -> bool:
        """Return True when working memory exceeds the configured session limit."""
        snapshot = self.snapshot(state)
        return snapshot.tokens_used > snapshot.token_limit
