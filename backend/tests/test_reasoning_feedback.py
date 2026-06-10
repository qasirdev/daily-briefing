"""Tests for reasoning-level feedback API."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import create_app
from backend.settings import Settings

if TYPE_CHECKING:
    from fastapi import FastAPI

TRACE_ID = "c" * 32


@pytest.fixture
def app() -> FastAPI:
    return create_app(Settings(app_env="development"))


@pytest.mark.asyncio
async def test_reasoning_feedback_endpoint(app: FastAPI) -> None:
    with patch(
        "backend.api.v1.feedback.store_reasoning_feedback",
        new_callable=AsyncMock,
        return_value="lesson-123",
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/feedback/reasoning",
                json={
                    "user_id": "user-1",
                    "briefing_id": "brief-1",
                    "trace_id": TRACE_ID,
                    "agent_id": "focus",
                    "rating": "correct",
                    "comment": "Good prioritization",
                },
            )
    assert response.status_code == 201
    payload = response.json()
    assert payload["stored"] is True
    assert payload["lesson_id"] == "lesson-123"


@pytest.mark.asyncio
async def test_reasoning_feedback_rejects_short_trace_id(app: FastAPI) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/feedback/reasoning",
            json={
                "user_id": "user-1",
                "briefing_id": "brief-1",
                "trace_id": "short",
                "agent_id": "focus",
                "rating": "incorrect",
            },
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reasoning_feedback_rating_only(app: FastAPI) -> None:
    with patch(
        "backend.api.v1.feedback.store_reasoning_feedback",
        new_callable=AsyncMock,
        return_value="lesson-456",
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/feedback/reasoning",
                json={
                    "user_id": "user-1",
                    "briefing_id": "brief-1",
                    "trace_id": TRACE_ID,
                    "agent_id": "critic",
                    "rating": "partial",
                },
            )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_store_reasoning_feedback_calls_episodic() -> None:
    from backend.feedback.reasoning import store_reasoning_feedback
    from backend.schemas.reasoning_feedback import ReasoningFeedbackRequest

    mock_store = AsyncMock()
    mock_store.store_lesson = AsyncMock(return_value="uuid-lesson")

    body = ReasoningFeedbackRequest(
        user_id="user-1",
        briefing_id="brief-1",
        trace_id=TRACE_ID,
        agent_id="focus",
        rating="correct",
        comment="Accurate reasoning",
    )
    lesson_id = await store_reasoning_feedback(body, store=mock_store)
    assert lesson_id == "uuid-lesson"
    mock_store.store_lesson.assert_awaited_once()
    call_kwargs = mock_store.store_lesson.await_args.kwargs
    assert call_kwargs["metadata"]["feedback_type"] == "reasoning_feedback"


def test_hitl_feedback_layer_implemented() -> None:
    from backend.security.hitl import get_layer

    layer = get_layer("feedback")
    assert layer is not None
    assert layer.status == "implemented"
    assert layer.test_module == "backend/tests/test_reasoning_feedback.py"
