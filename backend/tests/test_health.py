"""Health endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_metrics_endpoint_includes_cache_and_memory_metrics(client: AsyncClient) -> None:
    response = await client.get("/metrics/", follow_redirects=True)
    assert response.status_code == 200
    body = response.text
    assert "llm_cache_hit_rate" in body
    assert "llm_cache_hit_total" in body
    assert "llm_cache_miss_total" in body
    assert "prompt_cache_hits_total" in body
    assert "cached_tokens_saved_total" in body
    assert "token_cost_per_request" in body
    assert "working_memory_utilization" in body
    assert "memory_reads_total" in body
