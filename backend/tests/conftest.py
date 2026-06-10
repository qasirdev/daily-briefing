"""Shared pytest fixtures."""

from collections.abc import AsyncGenerator, Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.llm.models import LLMResponse
from backend.main import create_app
from backend.mcp.calendar import CalendarMCPClient
from backend.mcp.postgres import PostgresMCPClient
from backend.settings import Settings, get_settings


@pytest.fixture
def mock_openrouter() -> AsyncMock:
    """Mock LLM API responses with realistic token counts."""
    mock = AsyncMock(
        return_value=LLMResponse(
            content='{"summary": "Test briefing"}',
            model_used="openai/gpt-4o-mini",
            tokens_used=42,
            prompt_tokens=30,
            completion_tokens=12,
            cost_usd=0.001,
            latency_ms=5,
        ),
    )
    return mock


@pytest.fixture
def mock_postgresql_mcp() -> PostgresMCPClient:
    """Simulate PostgreSQL MCP tool responses."""
    client = PostgresMCPClient(host="localhost", port=5443)
    client.query = AsyncMock(return_value={"rows": []})  # type: ignore[method-assign]
    return client


@pytest.fixture
def mock_calendar_mcp() -> CalendarMCPClient:
    """Simulate Google Calendar MCP with test events."""
    client = CalendarMCPClient(host="localhost", port=5444)
    client.get_events = AsyncMock(return_value=[])  # type: ignore[method-assign]
    return client


@pytest.fixture
def mock_otlp_collector() -> MagicMock:
    """Capture OpenTelemetry spans without external dependencies."""
    collector = MagicMock()
    collector.spans = []
    collector.export = MagicMock(side_effect=lambda spans: collector.spans.extend(spans))
    return collector


@pytest.fixture
def mock_local_llm() -> AsyncMock:
    """Simulate LiteLLM fallback for offline testing."""
    return AsyncMock(
        return_value=LLMResponse(
            content='{"summary": "Local fallback"}',
            model_used="local/test",
            tokens_used=8,
            latency_ms=2,
        ),
    )


@pytest.fixture(autouse=True)
def _deterministic_embeddings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Keep semantic memory tests offline regardless of developer .env."""
    monkeypatch.setenv("EMBEDDING_PROVIDER", "deterministic")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> Iterator[None]:
    """Prevent rate-limit state leaking between tests."""
    from backend.security.rate_limit import limiter

    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        app_env="development",
        app_debug=False,
        jwt_secret_key="test-jwt-secret-key-for-unit-tests-only-32chars",
    )


@pytest.fixture
def app(test_settings: Settings) -> FastAPI:
    return create_app(test_settings)


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
