"""E2E degraded briefing scenarios."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_briefing_returns_degraded_status(client: AsyncClient) -> None:
    mock_state = {
        "status": "degraded",
        "final_briefing": "<p>Partial briefing</p>",
        "total_tokens": 12,
        "consent_required": False,
        "consent_context": None,
        "consent_request": None,
    }
    with patch("backend.api.v1.briefing.build_briefing_graph") as build_graph:
        graph = AsyncMock()
        graph.ainvoke.return_value = mock_state
        build_graph.return_value = graph
        response = await client.post(
            "/api/v1/briefing/generate",
            json={"user_id": "user-1"},
        )
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
