"""LangGraph builder for the briefing orchestration pipeline."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Literal

import structlog
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from backend.agents.calendar.node import calendar_agent_node
from backend.agents.critic.node import critic_agent_node
from backend.agents.focus.node import focus_agent_node
from backend.agents.orchestrator.node import orchestrator_present_node, orchestrator_route_node
from backend.agents.task.node import task_agent_node
from backend.dependencies import MCPClients, build_llm_router
from backend.graph.state import BriefingGraphState
from backend.llm.router import LLMRouter
from backend.schemas.envelope import AgentResultEnvelope
from backend.settings import Settings, get_settings

logger = structlog.get_logger()


def should_circuit_break(state: BriefingGraphState, settings: Settings) -> bool:
    """Return True when token budget or graph timeout exceeded."""
    total_tokens = state.get("total_tokens", 0)
    if total_tokens > settings.token_budget_max * 2:
        return True
    started = state.get("graph_started_at")
    if started is not None and (time.perf_counter() - started) > settings.graph_timeout_seconds:
        return True
    return False


def build_briefing_graph(
    mcp: MCPClients,
    llm: LLMRouter | None = None,
    settings: Settings | None = None,
) -> CompiledStateGraph[Any, Any, Any]:
    """Build and compile the full MVP2 briefing graph."""
    resolved_settings = settings or get_settings()
    resolved_llm = llm or build_llm_router(resolved_settings)

    async def parallel_task_calendar_node(state: BriefingGraphState) -> dict[str, Any]:
        task_update, calendar_update = await asyncio.gather(
            task_agent_node(state, mcp.postgres),
            calendar_agent_node(state, mcp.calendar),
        )
        merged: dict[str, Any] = {**task_update, **calendar_update}
        if calendar_update.get("consent_required"):
            merged["consent_required"] = True
            merged["consent_context"] = calendar_update.get("consent_context")
        return merged

    async def focus_wrapper(state: BriefingGraphState) -> dict[str, Any]:
        return await focus_agent_node(state, resolved_llm)

    async def dlq_handler_node(state: BriefingGraphState) -> dict[str, Any]:
        trace_id = state.get("trace_id", "0" * 32)
        event = {
            "trace_id": trace_id,
            "reason": "circuit_breaker",
            "agent": state.get("current_agent", "unknown"),
        }
        logger.error("dlq_event_recorded", **event)
        events = list(state.get("dlq_events", []))
        events.append(event)
        return {
            "status": "failure",
            "final_briefing": "",
            "dlq_events": events,
            "current_agent": "dlq_handler",
        }

    def route_after_parallel(
        state: BriefingGraphState,
    ) -> Literal["dlq_handler", "focus_agent", "orchestrator_present"]:
        if should_circuit_break(state, resolved_settings):
            return "dlq_handler"
        if state.get("consent_required"):
            return "orchestrator_present"
        for key in ("task_result", "calendar_result"):
            envelope = state.get(key)
            if (
                isinstance(envelope, AgentResultEnvelope)
                and envelope.status == "escalated"
                and envelope.escalation
                and envelope.escalation.reason == "consent_required"
            ):
                return "orchestrator_present"
        return "focus_agent"

    def route_after_focus(state: BriefingGraphState) -> Literal["dlq_handler", "critic_agent"]:
        if should_circuit_break(state, resolved_settings):
            return "dlq_handler"
        return "critic_agent"

    graph = StateGraph(BriefingGraphState)
    graph.add_node("orchestrator_route", orchestrator_route_node)
    graph.add_node("parallel_task_calendar", parallel_task_calendar_node)
    graph.add_node("focus_agent", focus_wrapper)
    graph.add_node("critic_agent", critic_agent_node)
    graph.add_node("orchestrator_present", orchestrator_present_node)
    graph.add_node("dlq_handler", dlq_handler_node)

    graph.add_edge(START, "orchestrator_route")
    graph.add_edge("orchestrator_route", "parallel_task_calendar")
    graph.add_conditional_edges(
        "parallel_task_calendar",
        route_after_parallel,
        {
            "focus_agent": "focus_agent",
            "orchestrator_present": "orchestrator_present",
            "dlq_handler": "dlq_handler",
        },
    )
    graph.add_conditional_edges(
        "focus_agent",
        route_after_focus,
        {"critic_agent": "critic_agent", "dlq_handler": "dlq_handler"},
    )
    graph.add_edge("critic_agent", "orchestrator_present")
    graph.add_edge("orchestrator_present", END)
    graph.add_edge("dlq_handler", END)

    return graph.compile()
