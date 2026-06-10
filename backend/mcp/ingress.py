"""MCP ingress helpers — validation, spotlighting, and tool policy (Gaps #114, #117)."""

from __future__ import annotations

from typing import Any

from backend.kernel.tool_manager import ToolManager
from backend.security.spotlighting import spotlight_external_content

_tool_manager = ToolManager()


def reset_mcp_tool_session(session_id: str) -> None:
    """Reset per-request MCP tool call counters."""
    _tool_manager.reset_session(session_id)


def authorize_mcp_tool(*, agent_id: str, tool: str, session_id: str) -> None:
    """Enforce per-agent tool allowlist and chaining limits."""
    _tool_manager.authorize_tool(agent_id=agent_id, tool=tool, session_id=session_id)


def validate_calendar_response(response: dict[str, Any]) -> dict[str, Any]:
    """Validate and sanitize calendar MCP payloads."""
    return _tool_manager.validate_response("calendar.read_events", response)


def validate_task_response(response: dict[str, Any]) -> dict[str, Any]:
    """Validate and sanitize task MCP payloads."""
    return _tool_manager.validate_response("tasks.list", response)


def spotlight_task_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Wrap untrusted task text fields in spotlight markers."""
    spotlighted: list[dict[str, object]] = []
    for row in rows:
        item = dict(row)
        title = item.get("title")
        if isinstance(title, str) and title.strip():
            item["title"] = spotlight_external_content(title)
        spotlighted.append(item)
    return spotlighted
