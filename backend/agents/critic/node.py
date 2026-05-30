"""Critic agent placeholder until MVP 3."""

from __future__ import annotations

import time
from typing import Any

from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata


async def critic_agent_node(state: BriefingGraphState) -> dict[str, Any]:
    """Pass-through critic placeholder for MVP 2 graph wiring."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    execution_ms = int((time.perf_counter() - start) * 1000)
    envelope = AgentResultEnvelope(
        agent_id="critic",
        canonical_role="critic",
        status="success",
        result={"approved": True, "revision_required": False},
        metadata=ExecutionMetadata(
            execution_ms=execution_ms,
            tokens_used=0,
            model_used="none",
            prompt_version="v1.5.0",
            trace_id=trace_id,
            data_classification="internal",
        ),
    )
    return {"critic_result": envelope, "current_agent": "critic"}
