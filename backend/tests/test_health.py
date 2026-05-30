"""Health endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_includes_trace_id_header(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert "x-trace-id" in response.headers

