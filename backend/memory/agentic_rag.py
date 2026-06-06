"""Agentic RAG — dynamic retrieval decisions (Gaps #33, #37)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from backend.settings import Settings, get_settings

MemoryLayer = Literal["semantic", "procedural", "episodic"]
RetrievalDecisionKind = Literal["skip", "partial", "full", "refine"]


@dataclass(frozen=True, slots=True)
class RetrievalDecision:
    """Whether and which memory layers to query for an agent turn."""

    kind: RetrievalDecisionKind
    layers: frozenset[MemoryLayer]
    query: str
    reason: str
    refinement_pass: int = 0


def decide_retrieval(
    *,
    user_id: str,
    agent_id: str,
    query_text: str,
    task_count: int = 0,
    event_count: int = 0,
    working_context_count: int = 0,
    has_prior_briefings: bool = False,
    settings: Settings | None = None,
) -> RetrievalDecision:
    """Decide whether, when, and which CoALA layers to retrieve."""
    resolved = settings or get_settings()
    query = query_text.strip()

    if not user_id:
        return RetrievalDecision(
            kind="skip",
            layers=frozenset(),
            query=query,
            reason="anonymous_user_no_durable_memory",
        )

    if not resolved.enable_agentic_rag:
        return RetrievalDecision(
            kind="full",
            layers=frozenset({"semantic", "procedural", "episodic"}),
            query=query or "daily briefing focus plan",
            reason="agentic_rag_disabled_legacy_mode",
        )

    procedural_only: frozenset[MemoryLayer] = frozenset({"procedural"})
    full_layers: frozenset[MemoryLayer] = frozenset({"semantic", "procedural", "episodic"})

    if not query and task_count == 0 and event_count == 0 and working_context_count == 0:
        return RetrievalDecision(
            kind="partial",
            layers=procedural_only,
            query="daily briefing focus plan",
            reason="empty_context_procedural_skills_only",
        )

    if not has_prior_briefings and not working_context_count:
        layers: frozenset[MemoryLayer] = frozenset({"procedural", "episodic"})
        return RetrievalDecision(
            kind="partial",
            layers=layers,
            query=query or "daily briefing focus plan",
            reason="first_session_skip_semantic_history",
        )

    if task_count + event_count >= 3 or working_context_count >= 2:
        return RetrievalDecision(
            kind="full",
            layers=full_layers,
            query=query or "daily briefing focus plan",
            reason="rich_mcp_and_working_context",
        )

    return RetrievalDecision(
        kind="partial",
        layers=frozenset({"semantic", "procedural"}),
        query=query or "daily briefing focus plan",
        reason="moderate_context_precision_retrieval",
    )


def refine_query(
    *,
    base_query: str,
    semantic_hit_count: int,
    refinement_pass: int,
    max_passes: int = 2,
) -> tuple[str, int, bool]:
    """Iteratively broaden query when semantic search under-delivers."""
    if semantic_hit_count > 0 or refinement_pass >= max_passes:
        return base_query, refinement_pass, False

    broadened = f"{base_query} | historical briefing patterns | user preferences"
    return broadened, refinement_pass + 1, True


def should_retry_retrieval(
    *,
    decision: RetrievalDecision,
    semantic_hit_count: int,
    refinement_pass: int,
    max_passes: int = 2,
) -> bool:
    """True when agentic RAG should run a refinement pass."""
    if "semantic" not in decision.layers:
        return False
    if semantic_hit_count > 0:
        return False
    return refinement_pass < max_passes
