"""MCP client exceptions and base implementation."""

from __future__ import annotations

import re
from typing import Any, cast

import httpx

from backend.metrics import observe_mcp_call
from backend.telemetry import start_async_span

MCP_TIMEOUT_SECONDS = 30.0


class MCPError(Exception):
    """Base MCP error."""


class MCPTimeoutError(MCPError):
    """MCP operation timed out."""


class MCPPermissionError(MCPError):
    """Permission denied by MCP server."""


class MCPConsentRequired(MCPError):
    """User consent required for MCP access."""


class MCPClient:
    """HTTP JSON client for local MCP tool servers."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        timeout: float = MCP_TIMEOUT_SECONDS,
        server_name: str | None = None,
    ) -> None:
        self._base_url = f"http://{host}:{port}"
        self._timeout = timeout
        self._server_label = server_name or host
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def call_tool(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Invoke an MCP tool and return parsed JSON payload."""
        server = self._server_label
        async with start_async_span(
            f"mcp.{server}.{tool_name}",
            mcp_server=server,
            mcp_tool=tool_name,
        ):
            with observe_mcp_call(server=server, tool=tool_name):
                try:
                    response = await self._client.post(
                        f"{self._base_url}/tools/{tool_name}",
                        json={"arguments": args},
                    )
                except httpx.TimeoutException as exc:
                    msg = f"MCP tool '{tool_name}' timed out after {self._timeout}s"
                    raise MCPTimeoutError(msg) from exc
                except httpx.HTTPError as exc:
                    msg = f"MCP transport error for '{tool_name}': {exc}"
                    raise MCPError(msg) from exc

                if response.status_code == 408 or response.status_code == 504:
                    raise MCPTimeoutError(f"MCP tool '{tool_name}' timed out")

                if response.status_code == 403:
                    payload = response.json()
                    if payload.get("error") == "consent_required":
                        raise MCPConsentRequired(payload.get("message", "Consent required"))
                    raise MCPPermissionError(payload.get("message", "Permission denied"))

                if response.status_code >= 400:
                    detail = response.text
                    try:
                        detail = response.json().get("message", detail)
                    except ValueError:
                        pass
                    raise MCPError(f"MCP tool '{tool_name}' failed: {detail}")

                result: dict[str, Any] = cast(dict[str, Any], response.json())
                if result.get("error") == "consent_required":
                    raise MCPConsentRequired(str(result.get("message", "Consent required")))
                return result


FORBIDDEN_SQL = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def validate_read_query(sql: str, *, user_id: str | None) -> None:
    """Reject dangerous SQL and queries missing user scoping."""
    if not user_id:
        msg = "user_id is required for all MCP queries (RLS enforcement)"
        raise MCPPermissionError(msg)
    if FORBIDDEN_SQL.search(sql):
        msg = "Only read-only SELECT queries are permitted"
        raise MCPPermissionError(msg)
    if ":user_id" not in sql and "user_id" not in sql.lower():
        msg = "Query must filter by user_id for row-level security"
        raise MCPPermissionError(msg)
