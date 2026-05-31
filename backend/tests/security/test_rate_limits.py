"""Rate limiting enforcement tests."""

from typing import Any, cast
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from backend.main import create_app
from backend.settings import Settings
from backend.tests.http_client import api_client


@pytest.mark.asyncio
async def test_health_not_rate_limited() -> None:
    settings = Settings(jwt_secret_key="test-jwt-secret-key-for-unit-tests-only-32chars")
    async with api_client(settings) as client:
        for _ in range(5):
            response = await client.get("/health")
            assert response.status_code == 200


@pytest.mark.asyncio
async def test_briefing_rate_limit_returns_429() -> None:
    settings = Settings(jwt_secret_key="test-jwt-secret-key-for-unit-tests-only-32chars")
    app = create_app(settings)
    limiter = app.state.limiter
    original = limiter._key_func

    def fixed_key(_request: object) -> str:
        return "rate-limit-test-client"

    limiter._key_func = fixed_key
    try:
        transport = httpx.ASGITransport(app=app)
        mock_state = {
            "status": "success",
            "final_briefing": "<p>ok</p>",
            "total_tokens": 0,
        }
        with (
            patch("backend.api.v1.briefing.build_mcp_clients") as build_mcp,
            patch("backend.api.v1.briefing.build_briefing_graph") as build_graph,
        ):
            mcp = AsyncMock()
            mcp.close = AsyncMock()
            build_mcp.return_value = mcp
            graph = AsyncMock()
            graph.ainvoke.return_value = mock_state
            build_graph.return_value = graph
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                statuses: list[int] = []
                for _ in range(12):
                    response = await client.post(
                        "/api/v1/briefing/generate",
                        json={"user_id": "user-1"},
                    )
                    statuses.append(response.status_code)
                assert 429 in statuses
    finally:
        limiter._key_func = cast(Any, original)
        limiter.reset()
