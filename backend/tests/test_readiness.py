"""Readiness probe tests."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from backend.health.checks import HealthCheckResult, ReadinessResponse


@pytest.mark.asyncio
async def test_readiness_returns_checks(client: AsyncClient) -> None:
    report = ReadinessResponse(
        status="healthy",
        checks=[
            HealthCheckResult(name="postgres_mcp", status="healthy", latency_ms=1),
        ],
    )
    with patch(
        "backend.health.router.run_readiness_checks",
        AsyncMock(return_value=report),
    ):
        response = await client.get("/health/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["checks"]


@pytest.mark.asyncio
async def test_readiness_unhealthy_returns_503(client: AsyncClient) -> None:
    report = ReadinessResponse(
        status="unhealthy",
        checks=[
            HealthCheckResult(
                name="postgres_mcp",
                status="unhealthy",
                latency_ms=5,
                detail="connection refused",
            ),
        ],
    )
    with patch(
        "backend.health.router.run_readiness_checks",
        AsyncMock(return_value=report),
    ):
        response = await client.get("/health/ready")
    assert response.status_code == 503
