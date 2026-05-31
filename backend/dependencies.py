"""FastAPI dependency injection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from backend.llm.router import LLMRouter
from backend.mcp.calendar import CalendarMCPClient
from backend.mcp.calendar_stdio import CalendarMCPStdioClient
from backend.mcp.postgres import PostgresMCPClient
from backend.mcp.postgres_stdio import PostgresMCPStdioClient
from backend.settings import Settings, get_settings


@runtime_checkable
class PostgresMCPProtocol(Protocol):
    async def list_tables(self) -> dict[str, object]: ...

    async def query(
        self,
        *,
        sql: str,
        user_id: str,
        params: dict[str, object] | None = None,
    ) -> dict[str, object]: ...

    async def insert(
        self,
        *,
        table: str,
        data: dict[str, object],
        user_id: str,
    ) -> dict[str, object]: ...

    async def close(self) -> None: ...


@runtime_checkable
class CalendarMCPProtocol(Protocol):
    async def list_calendars(self, *, user_id: str) -> dict[str, object]: ...

    async def get_events(
        self,
        *,
        user_id: str,
        target_date: object,
        calendar_id: str = "primary",
    ) -> list[object]: ...

    async def close(self) -> None: ...


@dataclass
class MCPClients:
    """Bundle of MCP clients for graph nodes."""

    postgres: PostgresMCPProtocol
    calendar: CalendarMCPProtocol

    async def close(self) -> None:
        await self.postgres.close()
        await self.calendar.close()


def build_mcp_clients(settings: Settings | None = None) -> MCPClients:
    """Create MCP clients from settings."""
    resolved = settings or get_settings()
    if resolved.mcp_transport == "stdio":
        return MCPClients(
            postgres=PostgresMCPStdioClient(resolved),
            calendar=CalendarMCPStdioClient(resolved),
        )
    return MCPClients(
        postgres=PostgresMCPClient(
            host=resolved.postgres_mcp_host,
            port=resolved.postgres_mcp_port,
            server_name="postgres",
        ),
        calendar=CalendarMCPClient(
            host=resolved.calendar_mcp_host,
            port=resolved.calendar_mcp_port,
            server_name="calendar",
        ),
    )


def build_llm_router(settings: Settings | None = None) -> LLMRouter:
    return LLMRouter(settings or get_settings())
