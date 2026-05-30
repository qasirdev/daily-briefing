"""Orchestrator supervisor nodes."""

from __future__ import annotations

import time
from typing import Any, Literal

import structlog

from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.security.sanitization import sanitize_markdown

logger = structlog.get_logger()


def _collect_escalations(state: BriefingGraphState) -> list[AgentResultEnvelope]:
    escalated: list[AgentResultEnvelope] = []
    for key in ("task_result", "calendar_result", "focus_result", "critic_result"):
        envelope = state.get(key)
        if isinstance(envelope, AgentResultEnvelope) and envelope.status == "escalated":
            escalated.append(envelope)
    return escalated


async def orchestrator_route_node(state: BriefingGraphState) -> dict[str, Any]:
    """Initialize routing phase and detect early consent requirements."""
    trace_id = state.get("trace_id", "0" * 32)
    logger.info("orchestrator_route_started", trace_id=trace_id)
    return {
        "current_agent": "orchestrator_route",
        "status": "pending",
        "revision_count": state.get("revision_count", 0),
    }


async def orchestrator_present_node(state: BriefingGraphState) -> dict[str, Any]:
    """Synthesize sanitized markdown briefing from agent JSON results."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    escalations = _collect_escalations(state)

    if state.get("consent_required"):
        execution_ms = int((time.perf_counter() - start) * 1000)
        return {
            "status": "degraded",
            "final_briefing": "",
            "consent_required": True,
            "orchestrator_result": AgentResultEnvelope(
                agent_id="orchestrator",
                canonical_role="supervisor",
                status="success",
                result={"awaiting_consent": True},
                metadata=ExecutionMetadata(
                    execution_ms=execution_ms,
                    tokens_used=state.get("total_tokens", 0),
                    model_used="none",
                    prompt_version="v1.5.0",
                    trace_id=trace_id,
                    data_classification="internal",
                ),
            ),
        }

    sections: list[str] = ["<h1>Daily Briefing</h1>"]

    task_result = state.get("task_result")
    if isinstance(task_result, AgentResultEnvelope) and task_result.status == "success" and task_result.result:
        tasks = task_result.result.get("tasks", [])
        if isinstance(tasks, list) and tasks:
            items = "".join(
                f"<li>{task.get('title', 'Task')} ({task.get('priority', 'medium')})</li>"
                for task in tasks
                if isinstance(task, dict)
            )
            sections.append(f"<h2>Tasks</h2><ul>{items}</ul>")

    calendar_result = state.get("calendar_result")
    if (
        isinstance(calendar_result, AgentResultEnvelope)
        and calendar_result.status == "success"
        and calendar_result.result
    ):
        events = calendar_result.result.get("events", [])
        if isinstance(events, list) and events:
            items = "".join(
                f"<li>{event.get('summary', 'Event')} — {event.get('start', '')}</li>"
                for event in events
                if isinstance(event, dict)
            )
            sections.append(f"<h2>Calendar</h2><ul>{items}</ul>")

    focus_result = state.get("focus_result")
    if (
        isinstance(focus_result, AgentResultEnvelope)
        and focus_result.status == "success"
        and focus_result.result
    ):
        plan = focus_result.result.get("plan", {})
        if isinstance(plan, dict):
            summary = plan.get("summary", "Focus plan generated.")
        else:
            summary = "Focus plan generated."
        sections.append(f"<h2>Focus Plan</h2><p>{summary}</p>")

    if escalations:
        sections.append("<p><strong>Note:</strong> Some components were degraded.</p>")

    raw_markdown = "".join(sections)
    briefing = sanitize_markdown(raw_markdown)

    status: Literal["success", "failure", "degraded"]
    if escalations and briefing:
        status = "degraded"
    elif escalations:
        status = "failure"
    else:
        status = "success"

    execution_ms = int((time.perf_counter() - start) * 1000)
    envelope = AgentResultEnvelope(
        agent_id="orchestrator",
        canonical_role="supervisor",
        status="success",
        result={"sections": len(sections), "escalations": len(escalations)},
        metadata=ExecutionMetadata(
            execution_ms=execution_ms,
            tokens_used=state.get("total_tokens", 0),
            model_used="none",
            prompt_version="v1.5.0",
            trace_id=trace_id,
            data_classification="confidential",
        ),
    )
    return {
        "final_briefing": briefing,
        "status": status,
        "orchestrator_result": envelope,
        "current_agent": "orchestrator_present",
    }
