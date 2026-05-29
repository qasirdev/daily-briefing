"""
Reference Implementation: Agent Node

This example demonstrates the standard pattern for a LangGraph node
in the AI Daily Briefing Assistant. It showcases strict typing,
AgentResultEnvelope usage, error handling, and OpenTelemetry context propagation.
"""

import time
from typing import cast
from pydantic import ValidationError

# ... dummy imports to represent the ecosystem
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata, EscalationPayload
from backend.graph.state import BriefingGraphState

async def example_agent_node(state: BriefingGraphState) -> AgentResultEnvelope:
    """Canonical structure for a Doer/Planner agent node."""
    start_time = time.perf_counter()
    tokens_used = 0
    
    try:
        # 1. Extract context
        user_id = state.get("user_id")
        trace_id = state.get("trace_id", "missing-trace")
        
        # 2. Perform work (e.g. call an MCP or LLM)
        # result, tokens = await llm_router.generate(...)
        result_data = {"example_key": "example_value"}
        tokens_used = 150
        
        # 3. Calculate execution time
        execution_ms = int((time.perf_counter() - start_time) * 1000)
        
        # 4. Return canonical success envelope
        return AgentResultEnvelope(
            agent_id="example_agent",
            canonical_role="doer",
            status="success",
            result=result_data,
            metadata=ExecutionMetadata(
                execution_ms=execution_ms,
                tokens_used=tokens_used,
                model_used="openai/gpt-4o-mini",
                prompt_version="v1.5.0",
                trace_id=trace_id,
                data_classification="internal"
            )
        )
        
    except Exception as e:
        # Calculate execution time for failure
        execution_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Return canonical failure envelope
        return AgentResultEnvelope(
            agent_id="example_agent",
            canonical_role="doer",
            status="escalated",
            escalation=EscalationPayload(
                reason="unexpected_error",
                target_agent="orchestrator",
                context=str(e)
            ),
            metadata=ExecutionMetadata(
                execution_ms=execution_ms,
                tokens_used=tokens_used,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id=state.get("trace_id", "unknown"),
                data_classification="internal"
            )
        )
