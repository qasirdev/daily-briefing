"""Verify testing.mdc shared mock fixtures are available."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.llm.models import LLMResponse
from backend.mcp.calendar import CalendarMCPClient
from backend.mcp.postgres import PostgresMCPClient


def test_mock_openrouter_returns_realistic_tokens(mock_openrouter: AsyncMock) -> None:
    response = mock_openrouter.return_value
    assert isinstance(response, LLMResponse)
    assert response.tokens_used > 0
    assert response.model_used == "openai/gpt-4o-mini"


@pytest.mark.asyncio
async def test_mock_postgresql_mcp_returns_rows(mock_postgresql_mcp: PostgresMCPClient) -> None:
    result = await mock_postgresql_mcp.query(sql="SELECT 1", user_id="user-1")
    assert result == {"rows": []}


@pytest.mark.asyncio
async def test_mock_calendar_mcp_returns_events(mock_calendar_mcp: CalendarMCPClient) -> None:
    events = await mock_calendar_mcp.get_events(user_id="user-1", target_date=date.today())
    assert events == []


def test_mock_otlp_collector_captures_spans(mock_otlp_collector: MagicMock) -> None:
    mock_otlp_collector.export(["span-a", "span-b"])
    assert mock_otlp_collector.spans == ["span-a", "span-b"]


@pytest.mark.asyncio
async def test_mock_local_llm_returns_local_model(mock_local_llm: AsyncMock) -> None:
    response = await mock_local_llm()
    assert "local" in response.model_used.lower()
