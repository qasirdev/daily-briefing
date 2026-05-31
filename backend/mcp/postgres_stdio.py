"""PostgreSQL MCP client over stdio (@modelcontextprotocol/server-postgres)."""

from __future__ import annotations

from typing import Any

from backend.mcp.client import MCPPermissionError, validate_read_query
from backend.mcp.postgres import ALLOWED_TABLES
from backend.mcp.stdio_transport import StdioMCPTransport, bind_user_id
from backend.settings import Settings, get_settings


class PostgresMCPStdioClient(StdioMCPTransport):
    """Stdio MCP client for PostgreSQL task data access."""

    def __init__(self, settings: Settings | None = None) -> None:
        resolved = settings or get_settings()
        postgres_url = resolved.resolved_mcp_postgres_url
        super().__init__(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-postgres", postgres_url],
            server_name="postgres",
            env={
                "NODE_TLS_REJECT_UNAUTHORIZED": "0",
                "NPM_CONFIG_CACHE": "/tmp/npm-cache",
            },
        )

    async def list_tables(self) -> dict[str, Any]:
        sql = (
            "SELECT table_name AS name, table_schema AS schema "
            "FROM information_schema.tables "
            "WHERE table_schema = 'public' "
            "AND table_name = ANY(ARRAY['tasks','user_preferences','dlq_events',"
            "'consent_records','consent_audit_log'])"
        )
        result = await self.call_tool("query", {"sql": sql})
        rows = result.get("rows", [])
        if isinstance(rows, list):
            tables = [
                {
                    "name": row.get("name"),
                    "schema": row.get("schema", "public"),
                }
                for row in rows
                if isinstance(row, dict)
            ]
            return {"tables": tables}
        return {"tables": []}

    async def query(
        self,
        *,
        sql: str,
        user_id: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        validate_read_query(sql, user_id=user_id)
        bound_sql = bind_user_id(sql, user_id)
        if params:
            for key, value in params.items():
                placeholder = f":{key}"
                if placeholder in bound_sql:
                    safe = str(value).replace("'", "''")
                    bound_sql = bound_sql.replace(placeholder, f"'{safe}'")
        result = await self.call_tool("query", {"sql": bound_sql})
        rows = result.get("rows", [])
        if not isinstance(rows, list):
            rows = []
        return {"rows": rows, "row_count": len(rows)}

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
        msg = "Insert via stdio PostgreSQL MCP is not supported; use SQLAlchemy persistence"
        raise MCPPermissionError(msg)
