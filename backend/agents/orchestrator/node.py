"""Orchestrator supervisor nodes."""

from __future__ import annotations

import json
import time
from typing import Any, Literal

import structlog

from backend.graph.state import BriefingGraphState
from backend.metrics import record_consent_request
from backend.schemas.consent import (
    DEFAULT_TTL_HOURS,
    ConsentPromptRequest,
    coerce_consent_service,
)
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.security.sanitization import sanitize_markdown

logger = structlog.get_logger()


def _success_result(envelope: AgentResultEnvelope | None) -> dict[str, object] | None:
    """Return the result dict when an envelope completed successfully."""
    if envelope is None or envelope.status != "success" or envelope.result is None:
        return None
    return envelope.result


def _collect_escalations(state: BriefingGraphState) -> list[AgentResultEnvelope]:
    escalated: list[AgentResultEnvelope] = []
    for key in ("task_result", "calendar_result", "focus_result", "critic_result"):
        envelope = state.get(key)
        if isinstance(envelope, AgentResultEnvelope) and envelope.status == "escalated":
            escalated.append(envelope)
    return escalated


def _parse_consent_context(context: str) -> dict[str, object]:
    try:
        parsed = json.loads(context)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {
        "service": "google_calendar",
        "scope": ["calendar.readonly"],
        "suggested_ttl_hours": DEFAULT_TTL_HOURS.get("google_calendar", 4),
        "message": context,
    }


def build_consent_prompt(state: BriefingGraphState) -> ConsentPromptRequest:
    """Build a JIT consent prompt from calendar escalation or state flags."""
    calendar = state.get("calendar_result")
    context_data: dict[str, object] = {}
    if isinstance(calendar, AgentResultEnvelope) and calendar.escalation:
        context_data = _parse_consent_context(calendar.escalation.context)

    service = coerce_consent_service(context_data.get("service", "google_calendar"))
    scope_raw = context_data.get("scope", ["calendar.readonly"])
    if isinstance(scope_raw, list):
        scope = [str(item) for item in scope_raw]
    else:
        scope = ["calendar.readonly"]
    ttl_raw = context_data.get("suggested_ttl_hours", DEFAULT_TTL_HOURS.get(service, 4))
    ttl = int(ttl_raw) if isinstance(ttl_raw, (int, float, str)) else DEFAULT_TTL_HOURS.get(service, 4)

    record_consent_request(mcp_server=service, outcome="requested")
    return ConsentPromptRequest(
        request_id=state.get("request_id", state.get("trace_id", "0" * 32)),
        service=service,
        scope=scope,
        suggested_ttl_hours=ttl,
        agent_requesting=str(context_data.get("agent_id", "calendar")),
        message=str(context_data.get("message", state.get("consent_context") or "")),
    )


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

    consent_escalation = any(
        envelope.escalation and envelope.escalation.reason == "consent_required"
        for envelope in escalations
    )
    if state.get("consent_required") or consent_escalation:
        consent_request = build_consent_prompt(state)
        execution_ms = int((time.perf_counter() - start) * 1000)
        partial_sections: list[str] = []
        task_payload = _success_result(state.get("task_result"))
        if task_payload is not None:
            partial_sections.append("tasks")
        return {
            "status": "awaiting_consent",
            "final_briefing": "",
            "consent_required": True,
            "consent_request": consent_request.model_dump(mode="json"),
            "orchestrator_result": AgentResultEnvelope(
                agent_id="orchestrator",
                canonical_role="supervisor",
                status="success",
                result={
                    "awaiting_consent": True,
                    "partial_components": partial_sections,
                },
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

    task_payload = _success_result(state.get("task_result"))
    if task_payload is not None:
        tasks = task_payload.get("tasks", [])
        if isinstance(tasks, list) and tasks:
            items = "".join(
                f"<li>{task.get('title', 'Task')} ({task.get('priority', 'medium')})</li>"
                for task in tasks
                if isinstance(task, dict)
            )
            sections.append(f"<h2>Tasks</h2><ul>{items}</ul>")

    calendar_payload = _success_result(state.get("calendar_result"))
    if calendar_payload is not None:
        events = calendar_payload.get("events", [])
        if isinstance(events, list) and events:
            items = "".join(
                f"<li>{event.get('summary', 'Event')} — {event.get('start', '')}</li>"
                for event in events
                if isinstance(event, dict)
            )
            sections.append(f"<h2>Calendar</h2><ul>{items}</ul>")

    focus_payload = _success_result(state.get("focus_result"))
    if focus_payload is not None:
        plan = focus_payload.get("plan", {})
        if isinstance(plan, dict):
            summary = plan.get("summary", "Focus plan generated.")
        else:
            summary = "Focus plan generated."
        sections.append(f"<h2>Focus Plan</h2><p>{summary}</p>")

    non_consent_escalations = [
        envelope
        for envelope in escalations
        if not (envelope.escalation and envelope.escalation.reason == "consent_required")
    ]
    if non_consent_escalations:
        sections.append("<p><strong>Note:</strong> Some components were degraded.</p>")

    raw_markdown = "".join(sections)
    briefing = sanitize_markdown(raw_markdown)

    status: Literal["success", "failure", "degraded", "awaiting_consent"]
    if non_consent_escalations and briefing:
        status = "degraded"
    elif non_consent_escalations:
        status = "failure"
    else:
        status = "success"

    execution_ms = int((time.perf_counter() - start) * 1000)
    envelope = AgentResultEnvelope(
        agent_id="orchestrator",
        canonical_role="supervisor",
        status="success",
        result={"sections": len(sections), "escalations": len(non_consent_escalations)},
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
