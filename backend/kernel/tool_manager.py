"""Sandboxed MCP execution and tool chaining policy (Gaps #28-29, #117)."""

from __future__ import annotations

from typing import Any

from backend.mcp.validator import MCPResponseValidator

MAX_SEQUENTIAL_TOOL_CALLS = 3

TOOL_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "calendar_agent": ("calendar.read_events",),
    "task_agent": ("tasks.list", "tasks.update"),
    "focus_agent": (),
}


class ToolManager:
    """Enforces allowlists and validates MCP responses."""

    def __init__(self) -> None:
        self._validator = MCPResponseValidator()
        self._call_counts: dict[str, int] = {}

    def reset_session(self, session_id: str) -> None:
        self._call_counts[session_id] = 0

    def authorize_tool(self, *, agent_id: str, tool: str, session_id: str) -> None:
        allowed = TOOL_ALLOWLIST.get(agent_id, ())
        if tool not in allowed:
            msg = f"Tool '{tool}' not allowed for agent '{agent_id}'"
            raise PermissionError(msg)
        count = self._call_counts.get(session_id, 0) + 1
        if count > MAX_SEQUENTIAL_TOOL_CALLS:
            msg = f"Tool chaining limit exceeded for session {session_id}"
            raise PermissionError(msg)
        self._call_counts[session_id] = count

    def validate_response(self, tool: str, response: dict[str, Any]) -> dict[str, Any]:
        result = self._validator.validate(tool, response)
        if not result.valid or result.sanitized_response is None:
            msg = "; ".join(result.issues) or "invalid MCP response"
            raise ValueError(msg)
        return result.sanitized_response
