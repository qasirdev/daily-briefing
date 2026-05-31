"""Stdio MCP transport for Option 1 Enterprise Hybrid."""

from __future__ import annotations

import json
import re
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from backend.mcp.client import MCPError, MCPTimeoutError
from backend.metrics import observe_mcp_call
from backend.telemetry import start_async_span

_UNSAFE_SQL = re.compile(r"[^a-zA-Z0-9_\-]")


def bind_user_id(sql: str, user_id: str) -> str:
    """Replace :user_id placeholder with a safely quoted literal for stdio MCP servers."""
    if not user_id or _UNSAFE_SQL.search(user_id):
        msg = "Invalid user_id for SQL binding"
        raise MCPError(msg)
    return sql.replace(":user_id", f"'{user_id}'")


class StdioMCPTransport:
    """Invoke MCP tools over stdio by spawning a subprocess per call."""

    def __init__(
        self,
        *,
        command: str,
        args: list[str],
        server_name: str,
        env: dict[str, str] | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._command = command
        self._args = args
        self._server_name = server_name
        self._env = env
        self._timeout = timeout

    async def close(self) -> None:
        return None

    async def call_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        server = self._server_name
        params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=self._env,
        )
        async with start_async_span(
            f"mcp.{server}.{tool_name}",
            mcp_server=server,
            mcp_tool=tool_name,
        ):
            with observe_mcp_call(server=server, tool=tool_name):
                try:
                    async with stdio_client(params) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            result = await session.call_tool(tool_name, arguments=args)
                except TimeoutError as exc:
                    msg = f"MCP tool '{tool_name}' timed out after {self._timeout}s"
                    raise MCPTimeoutError(msg) from exc
                except OSError as exc:
                    msg = f"MCP transport error for '{tool_name}': {exc}"
                    raise MCPError(msg) from exc

                if result.isError:
                    detail = " ".join(
                        block.text for block in result.content if hasattr(block, "text")
                    )
                    if "consent" in detail.lower():
                        from backend.mcp.client import MCPConsentRequired

                        raise MCPConsentRequired(detail or "Consent required")
                    raise MCPError(f"MCP tool '{tool_name}' failed: {detail}")

                return _content_to_dict(result.content)


def _content_to_dict(content: object) -> dict[str, Any]:
    texts: list[str] = []
    for block in content:  # type: ignore[attr-defined]
        text = getattr(block, "text", None)
        if isinstance(text, str):
            texts.append(text)
    if not texts:
        return {}

    combined = "\n".join(texts).strip()
    try:
        parsed = json.loads(combined)
        if isinstance(parsed, list):
            return {"rows": parsed, "row_count": len(parsed)}
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    return {"raw": combined}
