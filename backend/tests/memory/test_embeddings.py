"""Tests for semantic memory embeddings."""

import math
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.memory.embeddings import (
    deterministic_embedding,
    embed_text,
    embed_text_async,
)
from backend.settings import Settings


def test_deterministic_embedding_has_expected_dimensions() -> None:
    vector = deterministic_embedding("hello world", dimensions=8)
    assert len(vector) == 8


def test_deterministic_embedding_is_normalized() -> None:
    vector = deterministic_embedding("semantic memory test", dimensions=16)
    norm = math.sqrt(sum(value * value for value in vector))
    assert math.isclose(norm, 1.0, rel_tol=1e-6)


def test_embed_text_uses_settings_dimension() -> None:
    vector = embed_text("briefing summary", settings=Settings(semantic_memory_embedding_dim=32))
    assert len(vector) == 32


def test_deterministic_embedding_is_stable() -> None:
    first = deterministic_embedding("same input", dimensions=12)
    second = deterministic_embedding("same input", dimensions=12)
    assert first == second


@pytest.mark.asyncio
async def test_embed_text_async_uses_deterministic_by_default() -> None:
    settings = Settings(semantic_memory_embedding_dim=16, embedding_provider="deterministic")
    vector = await embed_text_async("daily briefing", settings=settings)
    assert len(vector) == 16
    assert vector == deterministic_embedding("daily briefing", dimensions=16)


@pytest.mark.asyncio
async def test_embed_text_async_rejects_empty_text_for_openrouter() -> None:
    settings = Settings(embedding_provider="openrouter")
    with pytest.raises(ValueError, match="empty text"):
        await embed_text_async("   ", settings=settings)


@pytest.mark.asyncio
async def test_embed_text_async_calls_openrouter_when_configured() -> None:
    settings = Settings(
        embedding_provider="openrouter",
        embedding_model="openai/text-embedding-3-small",
        semantic_memory_embedding_dim=4,
        openrouter_api_key="test-key",
    )
    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1, 0.2, 0.3, 0.4]
    mock_response = MagicMock()
    mock_response.data = [mock_embedding]

    mock_client = MagicMock()
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)

    with patch("backend.memory.embeddings._embedding_client", return_value=mock_client):
        vector = await embed_text_async("semantic query", settings=settings)

    assert vector == [0.1, 0.2, 0.3, 0.4]
    mock_client.embeddings.create.assert_awaited_once_with(
        model="openai/text-embedding-3-small",
        input="semantic query",
    )


@pytest.mark.asyncio
async def test_embed_text_async_validates_openrouter_dimensions() -> None:
    settings = Settings(
        embedding_provider="openrouter",
        semantic_memory_embedding_dim=4,
        openrouter_api_key="test-key",
    )
    mock_embedding = MagicMock()
    mock_embedding.embedding = [0.1, 0.2]
    mock_response = MagicMock()
    mock_response.data = [mock_embedding]

    mock_client = MagicMock()
    mock_client.embeddings.create = AsyncMock(return_value=mock_response)

    with patch("backend.memory.embeddings._embedding_client", return_value=mock_client):
        with pytest.raises(ValueError, match="Embedding dimension mismatch"):
            await embed_text_async("bad dimensions", settings=settings)
