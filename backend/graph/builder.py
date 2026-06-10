"""LangGraph builder for the briefing orchestration pipeline."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Hashable
from typing import Any, Literal, cast

import structlog
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from backend.agents.adversarial.node import adversarial_agent_node
from backend.agents.calendar.node import calendar_agent_node
from backend.agents.consensus.node import consensus_evaluator_node
from backend.agents.critic.node import critic_agent_node
from backend.agents.focus.node import focus_agent_node
from backend.agents.orchestrator.node import (
    human_escalation_node,
    orchestrator_present_node,
    orchestrator_route_node,
)
from backend.agents.task.node import task_agent_node
from backend.agents.verification.node import verification_agent_node
from backend.dependencies import MCPClients, build_llm_router
from backend.graph.dlq_handler import dlq_handler_node
from backend.graph.input_security_gate import input_security_gate_node
from backend.graph.state import BriefingGraphState
from backend.kernel.scheduler import Scheduler
from backend.llm.router import LLMRouter
from backend.schemas.envelope import AgentResultEnvelope
from backend.security.token_budget import (
    evaluate_token_budget,
    has_presentable_results,
    is_session_token_exceeded,
)
from backend.settings import Settings, get_settings

logger = structlog.get_logger()

MAX_VERIFICATION_RETRIES = 1
MAX_ADVERSARIAL_REGENERATIONS = 1
_kernel_scheduler = Scheduler()

ConsensusRoute = Literal["agreement", "minor_disagreement", "major_disagreement"]


def _is_graph_timeout(state: BriefingGraphState, settings: Settings) -> bool:
    started = state.get("graph_started_at")
    return started is not None and (time.perf_counter() - started) > settings.graph_timeout_seconds


def should_route_to_dlq(state: BriefingGraphState, settings: Settings) -> bool:
    """Return True when the graph should abort to DLQ with no briefing."""
    if evaluate_token_budget(state) == "token_budget_exceeded":
        return True
    if _is_graph_timeout(state, settings):
        return True
    if is_session_token_exceeded(state, configured_max=settings.token_budget_max):
        return not has_presentable_results(state)
    return False


def should_circuit_break(state: BriefingGraphState, settings: Settings) -> bool:
    """Return True when further agent execution should stop."""
    if evaluate_token_budget(state) == "token_budget_exceeded":
        return True
    if _is_graph_timeout(state, settings):
        return True
    return is_session_token_exceeded(state, configured_max=settings.token_budget_max)


def route_consensus(state: BriefingGraphState) -> ConsensusRoute:
    """Route based on consensus evaluation result."""
    consensus_result = state.get("consensus_result")
    if not consensus_result:
        return "agreement"

    major_concerns = consensus_result.get("major_concerns", 0)
    moderate_concerns = consensus_result.get("moderate_concerns", 0)

    if isinstance(major_concerns, int) and major_concerns >= 2:
        return "major_disagreement"
    if isinstance(moderate_concerns, int) and moderate_concerns >= 1:
        return "minor_disagreement"
    return "agreement"


def build_briefing_graph(
    mcp: MCPClients,
    llm: LLMRouter | None = None,
    settings: Settings | None = None,
) -> CompiledStateGraph[Any, Any, Any]:
    """Build and compile the full briefing graph."""
    resolved_settings = settings or get_settings()
    resolved_llm = llm or build_llm_router(resolved_settings)
    consensus_enabled = resolved_settings.enable_consensus_workflow
    pipeline = _kernel_scheduler.pipeline(consensus_enabled=consensus_enabled)
    logger.debug("briefing_pipeline", phases=list(pipeline))

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
        update = await focus_agent_node(state, resolved_llm)
        prior_agent = state.get("current_agent")
        if prior_agent == "verification":
            update["verification_retry_count"] = state.get("verification_retry_count", 0) + 1
            update["regeneration_constraints"] = None
        elif prior_agent == "adversarial":
            update["adversarial_retry_count"] = state.get("adversarial_retry_count", 0) + 1
            update["regeneration_constraints"] = None
        return update

    async def critic_wrapper(state: BriefingGraphState) -> dict[str, Any]:
        return await critic_agent_node(state, resolved_llm)

    async def verification_wrapper(state: BriefingGraphState) -> dict[str, Any]:
        return await verification_agent_node(state, resolved_llm)

    async def adversarial_wrapper(state: BriefingGraphState) -> dict[str, Any]:
        return await adversarial_agent_node(state, resolved_llm)

    async def dlq_wrapper(state: BriefingGraphState) -> dict[str, Any]:
        return await dlq_handler_node(state, postgres=mcp.postgres)

    def route_after_input_security_gate(
        state: BriefingGraphState,
    ) -> Literal["dlq_handler", "focus_agent", "orchestrator_present"]:
        if state.get("failure_reason"):
            return "dlq_handler"
        if should_route_to_dlq(state, resolved_settings):
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

    def route_after_focus(
        state: BriefingGraphState,
    ) -> Literal["dlq_handler", "critic_agent", "verification_agent", "orchestrator_present"]:
        if should_route_to_dlq(state, resolved_settings):
            return "dlq_handler"
        if should_circuit_break(state, resolved_settings) and has_presentable_results(state):
            return "orchestrator_present"
        if consensus_enabled:
            return "verification_agent"
        return "critic_agent"

    def route_after_verification(
        state: BriefingGraphState,
    ) -> Literal["dlq_handler", "focus_agent", "adversarial_agent"]:
        verification = state.get("verification_result")
        if should_route_to_dlq(state, resolved_settings):
            return "dlq_handler"
        if isinstance(verification, AgentResultEnvelope) and verification.status == "escalated":
            escalation = verification.escalation
            if escalation and escalation.reason == "verification_failed":
                if state.get("verification_retry_count", 0) < MAX_VERIFICATION_RETRIES:
                    return "focus_agent"
        return "adversarial_agent"

    def route_after_adversarial(
        state: BriefingGraphState,
    ) -> Literal["dlq_handler", "critic_agent", "focus_agent", "orchestrator_present"]:
        adversarial = state.get("adversarial_result")
        if (
            _is_graph_timeout(state, resolved_settings)
            and has_presentable_results(state)
            and evaluate_token_budget(state) != "token_budget_exceeded"
        ):
            return "orchestrator_present"
        if should_route_to_dlq(state, resolved_settings):
            return "dlq_handler"
        if isinstance(adversarial, AgentResultEnvelope) and adversarial.status == "escalated":
            escalation = adversarial.escalation
            if escalation and escalation.reason == "adversarial_concerns":
                if state.get("adversarial_retry_count", 0) < MAX_ADVERSARIAL_REGENERATIONS:
                    return "focus_agent"
        return "critic_agent"

    def route_after_consensus(
        state: BriefingGraphState,
    ) -> Literal["dlq_handler", "human_escalation", "orchestrator_present"]:
        if (
            _is_graph_timeout(state, resolved_settings)
            and has_presentable_results(state)
            and evaluate_token_budget(state) != "token_budget_exceeded"
        ):
            return "orchestrator_present"
        if should_route_to_dlq(state, resolved_settings):
            return "dlq_handler"
        decision = route_consensus(state)
        if decision == "major_disagreement" and resolved_settings.consensus_human_escalation:
            return "human_escalation"
        return "orchestrator_present"

    def route_after_critic(
        state: BriefingGraphState,
    ) -> Literal["dlq_handler", "focus_agent", "consensus_evaluator", "orchestrator_present"]:
        critic = state.get("critic_result")
        if isinstance(critic, AgentResultEnvelope) and critic.status == "escalated":
            return "dlq_handler"
        if isinstance(critic, AgentResultEnvelope) and critic.result:
            if critic.result.get("revision_required") is True:
                return "focus_agent"
        if consensus_enabled:
            return "consensus_evaluator"
        return "orchestrator_present"

    graph = StateGraph(BriefingGraphState)
    graph.add_node("orchestrator_route", orchestrator_route_node)
    graph.add_node("parallel_task_calendar", parallel_task_calendar_node)
    graph.add_node("input_security_gate", input_security_gate_node)
    graph.add_node("focus_agent", focus_wrapper)
    graph.add_node("critic_agent", critic_wrapper)
    graph.add_node("orchestrator_present", orchestrator_present_node)
    graph.add_node("dlq_handler", dlq_wrapper)

    if consensus_enabled:
        graph.add_node("verification_agent", verification_wrapper)
        graph.add_node("adversarial_agent", adversarial_wrapper)
        graph.add_node("consensus_evaluator", consensus_evaluator_node)
        graph.add_node("human_escalation", human_escalation_node)

    graph.add_edge(START, "orchestrator_route")
    graph.add_edge("orchestrator_route", "parallel_task_calendar")
    graph.add_edge("parallel_task_calendar", "input_security_gate")
    graph.add_conditional_edges(
        "input_security_gate",
        route_after_input_security_gate,
        {
            "focus_agent": "focus_agent",
            "orchestrator_present": "orchestrator_present",
            "dlq_handler": "dlq_handler",
        },
    )

    if consensus_enabled:
        graph.add_conditional_edges(
            "focus_agent",
            route_after_focus,
            {
                "verification_agent": "verification_agent",
                "critic_agent": "critic_agent",
                "orchestrator_present": "orchestrator_present",
                "dlq_handler": "dlq_handler",
            },
        )
        graph.add_conditional_edges(
            "verification_agent",
            route_after_verification,
            {
                "focus_agent": "focus_agent",
                "adversarial_agent": "adversarial_agent",
                "dlq_handler": "dlq_handler",
            },
        )
        graph.add_conditional_edges(
            "adversarial_agent",
            route_after_adversarial,
            {
                "critic_agent": "critic_agent",
                "focus_agent": "focus_agent",
                "orchestrator_present": "orchestrator_present",
                "dlq_handler": "dlq_handler",
            },
        )
        graph.add_conditional_edges(
            "consensus_evaluator",
            route_after_consensus,
            {
                "human_escalation": "human_escalation",
                "orchestrator_present": "orchestrator_present",
                "dlq_handler": "dlq_handler",
            },
        )
        graph.add_edge("human_escalation", END)
    else:
        graph.add_conditional_edges(
            "focus_agent",
            route_after_focus,
            {
                "critic_agent": "critic_agent",
                "orchestrator_present": "orchestrator_present",
                "dlq_handler": "dlq_handler",
            },
        )

    critic_routes: dict[str, str] = {
        "focus_agent": "focus_agent",
        "orchestrator_present": "orchestrator_present",
        "dlq_handler": "dlq_handler",
    }
    if consensus_enabled:
        critic_routes["consensus_evaluator"] = "consensus_evaluator"
    graph.add_conditional_edges(
        "critic_agent",
        route_after_critic,
        cast(dict[Hashable, str], critic_routes),
    )
    graph.add_edge("orchestrator_present", END)
    graph.add_edge("dlq_handler", END)

    return graph.compile()
