"""MCP client package."""

from backend.mcp.calendar import CalendarEvent, CalendarMCPClient
from backend.mcp.client import (
    MCPClient,
    MCPConsentRequired,
    MCPError,
    MCPPermissionError,
    MCPTimeoutError,
)
from backend.mcp.postgres import PostgresMCPClient

__all__ = [
    "CalendarEvent",
    "CalendarMCPClient",
    "MCPClient",
    "MCPConsentRequired",
    "MCPError",
    "MCPPermissionError",
    "MCPTimeoutError",
    "PostgresMCPClient",
]
