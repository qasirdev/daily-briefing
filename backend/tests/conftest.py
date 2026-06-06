"""Shared pytest fixtures."""

from collections.abc import AsyncGenerator, Iterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.main import create_app
from backend.settings import Settings, get_settings


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
