"""Briefing API tests."""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.main import create_app
from backend.settings import Settings


@pytest.fixture
def api_app() -> FastAPI:
    settings = Settings(jwt_secret_key="test-jwt-secret-key-for-unit-tests-only-32chars")
    return create_app(settings)


@pytest.fixture
async def api_client(api_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=api_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_generate_briefing_success(api_client: AsyncClient) -> None:
    mock_result = {
        "status": "success",
        "final_briefing": "<p>Briefing</p>",
        "total_tokens": 10,
        "task_result": True,
        "calendar_result": True,
        "focus_result": True,
        "critic_result": True,
    }
    with patch("backend.api.v1.briefing.build_briefing_graph") as build_graph:
        graph = AsyncMock()
        graph.ainvoke.return_value = mock_result
        build_graph.return_value = graph
        response = await api_client.post(
            "/api/v1/briefing/generate",
            json={"user_id": "user-1"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert "x-trace-id" in response.headers


@pytest.mark.asyncio
async def test_generate_briefing_exposes_failure_reason(api_client: AsyncClient) -> None:
    mock_result = {
        "status": "failure",
        "final_briefing": "",
        "total_tokens": 0,
        "failure_reason": "security_violation_detected",
        "failure_message": "Briefing blocked: suspected prompt injection in calendar data.",
        "task_result": True,
        "calendar_result": True,
    }
    with patch("backend.api.v1.briefing.build_briefing_graph") as build_graph:
        graph = AsyncMock()
        graph.ainvoke.return_value = mock_result
        build_graph.return_value = graph
        response = await api_client.post(
            "/api/v1/briefing/generate",
            json={"user_id": "user-1"},
        )
    payload = response.json()
    assert payload["status"] == "failure"
    assert payload["failure_reason"] == "security_violation_detected"
    assert "calendar data" in payload["failure_message"]


@pytest.mark.asyncio
async def test_generate_briefing_unexpected_error_returns_failure_fields(
    api_client: AsyncClient,
) -> None:
    with patch("backend.api.v1.briefing.build_briefing_graph") as build_graph:
        graph = AsyncMock()
        graph.ainvoke.side_effect = RuntimeError("graph exploded")
        build_graph.return_value = graph
        response = await api_client.post(
            "/api/v1/briefing/generate",
            json={"user_id": "user-1"},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "failure"
    assert payload["failure_reason"] == "unexpected_error"
    assert payload["failure_message"]


@pytest.mark.asyncio
async def test_generate_briefing_requires_user_id(api_client: AsyncClient) -> None:
    response = await api_client.post("/api/v1/briefing/generate", json={})
    assert response.status_code == 422
