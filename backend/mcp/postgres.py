"""PostgreSQL MCP client."""

from __future__ import annotations

from typing import Any

from backend.mcp.client import (
    MCPClient,
    MCPPermissionError,
    validate_read_query,
)

ALLOWED_TABLES = frozenset({"tasks", "user_preferences", "dlq_events"})


class PostgresMCPClient(MCPClient):
    """MCP client for PostgreSQL task data access."""

    async def list_tables(self) -> dict[str, Any]:
        return await self.call_tool("list_tables", {})

    async def query(
        self,
        *,
        sql: str,
        user_id: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        validate_read_query(sql, user_id=user_id)
        arguments: dict[str, Any] = {"sql": sql, "user_id": user_id}
        if params:
            arguments["params"] = params
        return await self.call_tool("query", arguments)

    async def insert(
        self,
        *,
        table: str,
        data: dict[str, Any],
        user_id: str,
    ) -> dict[str, Any]:
        if table not in ALLOWED_TABLES:
            msg = f"Access denied to table: {table}"
            raise MCPPermissionError(msg)
        return await self.call_tool(
            "insert",
            {"table": table, "data": data, "user_id": user_id},
        )
