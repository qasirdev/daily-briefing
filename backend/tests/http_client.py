"""Async HTTP helpers for API tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from httpx import ASGITransport, AsyncClient

from backend.main import create_app
from backend.settings import Settings


@asynccontextmanager
async def api_client(settings: Settings | None = None) -> AsyncGenerator[AsyncClient, None]:
    """Yield an AsyncClient wired to the FastAPI app without sync TestClient."""
    app = create_app(settings or Settings())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
