"""E2E briefing generation flow."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata


@pytest.mark.asyncio
async def test_briefing_generate_happy_path(client: AsyncClient) -> None:
    mock_state: BriefingGraphState = {
        "status": "success",
        "final_briefing": "<p>Daily briefing</p>",
        "total_tokens": 42,
        "consent_required": False,
        "consent_context": None,
        "consent_request": None,
        "task_result": AgentResultEnvelope(
            agent_id="task",
            canonical_role="doer",
            status="success",
            result={"tasks": []},
            metadata=ExecutionMetadata(
                execution_ms=1,
                tokens_used=10,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id="c" * 32,
                data_classification="internal",
            ),
        ),
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
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["briefing"]
