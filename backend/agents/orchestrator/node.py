"""Orchestrator supervisor nodes."""

from __future__ import annotations

import json
import time
from typing import Any, Literal

import structlog

from backend.datetime_format import format_time_range
from backend.graph.state import BriefingGraphState
from backend.kernel.memory_manager import MemoryManager
from backend.mcp.ingress import reset_mcp_tool_session
from backend.metrics import record_consent_request
from backend.prompt_version import resolve_prompt_version
from backend.schemas.consent import (
    DEFAULT_TTL_HOURS,
    ConsentActionPayload,
    ConsentPromptRequest,
    coerce_consent_service,
)
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.security.pii import mask_pii
from backend.security.sanitization import sanitize_markdown
from backend.settings import get_settings

logger = structlog.get_logger()

_memory_manager = MemoryManager()

SERVICE_RESOURCE_LABELS: dict[str, str] = {
    "google_calendar": "primary calendar events",
    "postgres_mcp": "user tasks database",
}


def _render_focus_plan(plan: dict[str, object]) -> str:
    blocks = plan.get("time_blocks")
    block_count = len(blocks) if isinstance(blocks, list) else 0
    summary = plan.get("summary")
    if (
        not isinstance(summary, str)
        or not summary.strip()
        or summary.strip().startswith(("{", "```"))
    ):
        summary = (
            f"Today's focus plan includes {block_count} scheduled blocks "
            f"aligned with your calendar and tasks."
            if block_count
            else "Focus plan generated."
        )
    if isinstance(summary, str):
        summary = mask_pii(summary)
    parts = [f"<p>{summary}</p>"]
    if isinstance(blocks, list) and blocks:
        items = "".join(
            f"<li><strong>"
            f"{format_time_range(block.get('start', ''), block.get('end', ''))}"
            f"</strong>: "
            f"{mask_pii(str(block.get('activity', 'Scheduled block')))}</li>"
            for block in blocks
            if isinstance(block, dict)
        )
        if items:
            parts.append(f"<ul>{items}</ul>")
    return "".join(parts)


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
    if isinstance(ttl_raw, (int, float, str)):
        ttl = int(ttl_raw)
    else:
        ttl = DEFAULT_TTL_HOURS.get(service, 4)

    agent_id = str(context_data.get("agent_id", "calendar"))
    intent = str(context_data.get("intent", "read_events"))
    record_consent_request(mcp_server=service, outcome="requested")
    return ConsentPromptRequest(
        request_id=state.get("request_id", state.get("trace_id", "0" * 32)),
        service=service,
        scope=scope,
        suggested_ttl_hours=ttl,
        agent_requesting=agent_id,
        message=str(context_data.get("message", state.get("consent_context") or "")),
        action_payload=ConsentActionPayload(
            service=service,
            scope=scope,
            agent_id=agent_id,
            intent=intent,
            resource=str(context_data.get("resource", SERVICE_RESOURCE_LABELS.get(service, ""))),
        ),
    )


async def _distill_session_memory(state: BriefingGraphState) -> None:
    """Distill working memory into episodic lessons at session end."""
    settings = get_settings()
    if not settings.enable_episodic_memory:
        return

    user_id = state.get("user_id", "")
    if not user_id:
        return

    working_context = state.get("working_memory_context", [])
    if not isinstance(working_context, list) or not working_context:
        return

    session_id = state.get("request_id") or state.get("trace_id", "")
    if not session_id:
        return

    try:
        await _memory_manager.distill_session(
            user_id=user_id,
            session_id=session_id,
            working_context=working_context,
        )
    except Exception as exc:
        logger.warning(
            "session_memory_distillation_failed",
            trace_id=state.get("trace_id", "0" * 32),
            user_id=user_id,
            session_id=session_id,
            error=str(exc),
        )


async def human_escalation_node(state: BriefingGraphState) -> dict[str, Any]:
    """Pause briefing generation when consensus detects major disagreement."""
    trace_id = state.get("trace_id", "0" * 32)
    consensus = state.get("consensus_result") or {}
    logger.warning(
        "human_escalation_required",
        trace_id=trace_id,
        major_concerns=consensus.get("major_concerns", 0),
        agreement_level=consensus.get("agreement_level"),
    )
    return {
        "status": "awaiting_human_review",
        "current_agent": "human_escalation",
        "final_briefing": None,
    }


async def orchestrator_route_node(state: BriefingGraphState) -> dict[str, Any]:
    """Initialize routing phase and detect early consent requirements."""
    trace_id = state.get("trace_id", "0" * 32)
    request_id = state.get("request_id", trace_id)
    reset_mcp_tool_session(request_id)
    logger.info("orchestrator_route_started", trace_id=trace_id)
    return {
        "current_agent": "orchestrator_route",
        "status": "pending",
        "revision_count": state.get("revision_count", 0),
        **_memory_manager.working.initialize_state(state),
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
                    prompt_version=resolve_prompt_version("orchestrator"),
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
                f"<li>{mask_pii(str(task.get('title', 'Task')))} "
                f"({task.get('priority', 'medium')})</li>"
                for task in tasks
                if isinstance(task, dict)
            )
            sections.append(f"<h2>Tasks</h2><ul>{items}</ul>")

    calendar_payload = _success_result(state.get("calendar_result"))
    if calendar_payload is not None:
        events = calendar_payload.get("events", [])
        if isinstance(events, list) and events:
            items = "".join(
                f"<li>{mask_pii(str(event.get('summary', 'Event')))} — "
                f"{event.get('start', '')}</li>"
                for event in events
                if isinstance(event, dict)
            )
            sections.append(f"<h2>Calendar</h2><ul>{items}</ul>")

    focus_payload = _success_result(state.get("focus_result"))
    if focus_payload is not None:
        plan = focus_payload.get("plan", {})
        if isinstance(plan, dict):
            focus_html = _render_focus_plan(plan)
        else:
            focus_html = "<p>Focus plan generated.</p>"
        sections.append(f"<h2>Focus Plan</h2>{focus_html}")

    non_consent_escalations = [
        envelope
        for envelope in escalations
        if not (envelope.escalation and envelope.escalation.reason == "consent_required")
    ]
    if non_consent_escalations:
        sections.append("<p><strong>Note:</strong> Some components were degraded.</p>")

    raw_markdown = "".join(sections)
    briefing = sanitize_markdown(raw_markdown)

    consensus_without_critic = state.get("consensus_result") is not None and not isinstance(
        state.get("critic_result"),
        AgentResultEnvelope,
    )

    status: Literal["success", "failure", "degraded", "awaiting_consent"]
    if non_consent_escalations and briefing:
        status = "degraded"
    elif non_consent_escalations:
        status = "failure"
    elif consensus_without_critic and briefing:
        status = "degraded"
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
            prompt_version=resolve_prompt_version("orchestrator"),
            trace_id=trace_id,
            data_classification="confidential",
        ),
    )
    await _distill_session_memory(state)
    return {
        "final_briefing": briefing,
        "status": status,
        "orchestrator_result": envelope,
        "current_agent": "orchestrator_present",
    }
