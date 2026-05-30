"""Shared pytest fixtures."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.main import create_app
from backend.settings import Settings


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
