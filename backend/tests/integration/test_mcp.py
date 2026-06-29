"""MCP server integration tests."""

import httpx
import pytest
from pytest_httpx import HTTPXMock

from backend.mcp.client import MCPClient, MCPConsentRequired, MCPPermissionError, MCPTimeoutError
from backend.mcp.postgres import PostgresMCPClient


@pytest.mark.asyncio
async def test_mock_postgresql_mcp_fixture_returns_rows(
    mock_postgresql_mcp: PostgresMCPClient,
) -> None:
    result = await mock_postgresql_mcp.query(sql="SELECT 1", user_id="user-1")
    assert result == {"rows": []}


@pytest.mark.asyncio
async def test_postgres_list_tables(httpx_mock: HTTPXMock) -> None:
    client = PostgresMCPClient(host="localhost", port=5443)
    httpx_mock.add_response(json={"tables": [{"name": "tasks"}]})
    result = await client.list_tables()
    assert result["tables"][0]["name"] == "tasks"
    await client.close()


@pytest.mark.asyncio
async def test_postgres_rejects_query_without_user_id() -> None:
    client = PostgresMCPClient(host="localhost", port=5443)  # default 5433
    with pytest.raises(MCPPermissionError):
        await client.query(
            sql="SELECT * FROM tasks WHERE user_id = :user_id",
            user_id="",
        )
    await client.close()


@pytest.mark.asyncio
async def test_mcp_timeout(httpx_mock: HTTPXMock) -> None:
    client = MCPClient(host="localhost", port=5443, timeout=0.01)  # default 5433

    def raise_timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timeout")

    httpx_mock.add_callback(raise_timeout)
    with pytest.raises(MCPTimeoutError):
        await client.call_tool("query", {"user_id": "u1"})
    await client.close()


@pytest.mark.asyncio
async def test_consent_required_response(httpx_mock: HTTPXMock) -> None:
    client = MCPClient(host="localhost", port=5444)
    httpx_mock.add_response(
        status_code=403,
        json={"error": "consent_required", "message": "expired"},
    )
    with pytest.raises(MCPConsentRequired):
        await client.call_tool("get_events", {"user_id": "u1"})
    await client.close()
