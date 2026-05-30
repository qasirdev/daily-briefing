"""FastAPI dependency injection helpers."""

from dataclasses import dataclass

from backend.llm.router import LLMRouter
from backend.mcp.calendar import CalendarMCPClient
from backend.mcp.postgres import PostgresMCPClient
from backend.settings import Settings, get_settings


@dataclass
class MCPClients:
    """Bundle of MCP clients for graph nodes."""

    postgres: PostgresMCPClient
    calendar: CalendarMCPClient

    async def close(self) -> None:
        await self.postgres.close()
        await self.calendar.close()


def build_mcp_clients(settings: Settings | None = None) -> MCPClients:
    """Create MCP clients from settings."""
    resolved = settings or get_settings()
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
