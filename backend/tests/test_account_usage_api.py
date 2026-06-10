"""Account usage API tests."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.main import create_app
from backend.schemas.account_usage import AccountUsageResponse
from backend.settings import Settings


@pytest.fixture
def api_app() -> FastAPI:
    settings = Settings(
        jwt_secret_key="test-jwt-secret-key-for-unit-tests-only-32chars",
        openrouter_api_key="sk-test-openrouter",
    )
    return create_app(settings)


@pytest.fixture
async def api_client(api_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_account_usage_returns_openrouter_totals(api_client: AsyncClient) -> None:
    mock_usage = AccountUsageResponse(
        available=True,
        source="openrouter_key",
        label="daily-briefing",
        usage_all_time_usd=0.519,
        usage_daily_usd=0.012,
        usage_weekly_usd=0.042,
        usage_monthly_usd=0.057,
        limit_remaining_usd=4.5,
        is_free_tier=False,
    )
    with patch(
        "backend.api.v1.usage.fetch_openrouter_key_usage",
        new=AsyncMock(return_value=mock_usage),
    ):
        response = await api_client.get("/api/v1/usage/account")

    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is True
    assert payload["usage_all_time_usd"] == 0.519
    assert payload["usage_monthly_usd"] == 0.057
    assert payload["label"] == "daily-briefing"


@pytest.mark.asyncio
async def test_account_usage_unavailable_without_api_key() -> None:
    settings = Settings(
        jwt_secret_key="test-jwt-secret-key-for-unit-tests-only-32chars",
        openrouter_api_key="",
    )
    app = create_app(settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/usage/account")

    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is False
    assert "not configured" in payload["message"]
