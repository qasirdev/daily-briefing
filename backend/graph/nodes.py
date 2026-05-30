"""LangGraph node implementations."""

import time
from typing import Any, Literal

from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata

CanonicalRole = Literal["doer", "planner", "critic", "tool_operator", "supervisor"]


def _placeholder_envelope(
    *,
    agent_id: str,
    canonical_role: CanonicalRole,
    state: BriefingGraphState,
    result: dict[str, object] | None = None,
) -> AgentResultEnvelope:
    trace_id = state.get("trace_id", "0" * 32)
    return AgentResultEnvelope(
        agent_id=agent_id,
        canonical_role=canonical_role,
        status="success",
        result=result or {"status": "placeholder"},
        metadata=ExecutionMetadata(
            execution_ms=0,
            tokens_used=0,
            model_used="none",
            prompt_version="v1.5.0",
            trace_id=trace_id,
            data_classification="internal",
        ),
    )


async def orchestrator_node(state: BriefingGraphState) -> dict[str, Any]:
    """Orchestrator supervisor node — minimal MVP1 placeholder."""
    start = time.perf_counter()
    envelope = _placeholder_envelope(
        agent_id="orchestrator",
        canonical_role="supervisor",
        state=state,
        result={"message": "Orchestrator scaffold ready"},
    )
    execution_ms = int((time.perf_counter() - start) * 1000)
    updated = envelope.model_copy(
        update={
            "metadata": envelope.metadata.model_copy(update={"execution_ms": execution_ms}),
        },
    )
    return {
        "orchestrator_result": updated,
        "current_agent": "orchestrator",
        "status": "success",
        "final_briefing": None,
    }


async def task_node(state: BriefingGraphState) -> dict[str, Any]:
    """Task agent placeholder."""
    envelope = _placeholder_envelope(agent_id="task", canonical_role="doer", state=state)
    return {"task_result": envelope}


async def calendar_node(state: BriefingGraphState) -> dict[str, Any]:
    """Calendar agent placeholder."""
    return {
        "calendar_result": _placeholder_envelope(
            agent_id="calendar",
            canonical_role="doer",
            state=state,
        ),
    }


async def focus_node(state: BriefingGraphState) -> dict[str, Any]:
    """Focus agent placeholder."""
    envelope = _placeholder_envelope(agent_id="focus", canonical_role="planner", state=state)
    return {"focus_result": envelope}


async def critic_node(state: BriefingGraphState) -> dict[str, Any]:
    """Critic agent placeholder."""
    envelope = _placeholder_envelope(agent_id="critic", canonical_role="critic", state=state)
    return {"critic_result": envelope}
