"""Calendar agent LangGraph node."""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import Any

import structlog

from backend.graph.state import BriefingGraphState
from backend.mcp.calendar import CalendarMCPClient
from backend.mcp.client import MCPConsentRequired, MCPError, MCPTimeoutError
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata

logger = structlog.get_logger()


def _default_end(start_iso: str) -> str:
    try:
        start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        return (start + timedelta(minutes=30)).isoformat().replace("+00:00", "Z")
    except ValueError:
        return start_iso


async def calendar_agent_node(
    state: BriefingGraphState,
    calendar: CalendarMCPClient,
) -> dict[str, Any]:
    """Fetch today's calendar events via Google Calendar MCP."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    user_id = state.get("user_id", "")
    target_date = state.get("target_date") or date.today()

    logger.info("calendar_agent_started", trace_id=trace_id, user_id=user_id)

    try:
        events = await calendar.get_events(user_id=user_id, target_date=target_date)
        serialized = []
        for event in events:
            end = event.end or _default_end(event.start)
            serialized.append(
                {
                    "id": event.id,
                    "summary": event.summary,
                    "start": event.start,
                    "end": end,
                    "attendees": event.attendees,
                },
            )

        execution_ms = int((time.perf_counter() - start) * 1000)
        envelope = AgentResultEnvelope(
            agent_id="calendar",
            canonical_role="doer",
            status="success",
            result={"events": serialized},
            metadata=ExecutionMetadata(
                execution_ms=execution_ms,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id=trace_id,
                data_classification="confidential",
            ),
        )
        return {"calendar_result": envelope, "current_agent": "calendar"}

    except MCPConsentRequired as exc:
        execution_ms = int((time.perf_counter() - start) * 1000)
        envelope = AgentResultEnvelope(
            agent_id="calendar",
            canonical_role="doer",
            status="escalated",
            escalation=EscalationPayload(
                reason="consent_required",
                target_agent="orchestrator",
                context=str(exc),
            ),
            metadata=ExecutionMetadata(
                execution_ms=execution_ms,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id=trace_id,
                data_classification="internal",
            ),
        )
        return {
            "calendar_result": envelope,
            "current_agent": "calendar",
            "consent_required": True,
            "consent_context": str(exc),
        }

    except MCPTimeoutError as exc:
        execution_ms = int((time.perf_counter() - start) * 1000)
        logger.warning("calendar_agent_mcp_timeout", trace_id=trace_id, error=str(exc))
        envelope = AgentResultEnvelope(
            agent_id="calendar",
            canonical_role="doer",
            status="escalated",
            escalation=EscalationPayload(
                reason="mcp_timeout",
                target_agent="orchestrator",
                context=str(exc),
            ),
            metadata=ExecutionMetadata(
                execution_ms=execution_ms,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id=trace_id,
                data_classification="internal",
            ),
        )
        return {"calendar_result": envelope, "current_agent": "calendar"}

    except MCPError as exc:
        execution_ms = int((time.perf_counter() - start) * 1000)
        logger.warning("calendar_agent_mcp_error", trace_id=trace_id, error=str(exc))
        envelope = AgentResultEnvelope(
            agent_id="calendar",
            canonical_role="doer",
            status="escalated",
            escalation=EscalationPayload(
                reason="unexpected_error",
                target_agent="orchestrator",
                context=str(exc),
            ),
            metadata=ExecutionMetadata(
                execution_ms=execution_ms,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id=trace_id,
                data_classification="internal",
            ),
        )
        return {"calendar_result": envelope, "current_agent": "calendar"}
