"""Collect untrusted external text from agent envelopes for security scanning."""

from __future__ import annotations

import json

from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope

_MCP_SOURCES: tuple[tuple[str, str], ...] = (
    ("task", "task_result"),
    ("calendar", "calendar_result"),
)


def collect_mcp_external_texts(state: BriefingGraphState) -> dict[str, str]:
    """Return task and calendar payloads as JSON strings for injection scanning."""
    texts: dict[str, str] = {}
    for label, key in _MCP_SOURCES:
        envelope = state.get(key)
        if isinstance(envelope, AgentResultEnvelope) and envelope.result is not None:
            texts[label] = json.dumps(envelope.result, ensure_ascii=True)
    return texts


def collect_external_texts(state: BriefingGraphState) -> dict[str, str]:
    """Return all external agent payloads (task, calendar, focus) for review-stage scanning."""
    texts = collect_mcp_external_texts(state)
    focus = state.get("focus_result")
    if isinstance(focus, AgentResultEnvelope) and focus.result is not None:
        texts["focus"] = json.dumps(focus.result, ensure_ascii=True)
    return texts
