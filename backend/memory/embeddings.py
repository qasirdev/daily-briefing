"""Embedding helpers for semantic memory."""

from __future__ import annotations

import hashlib
import math
import time
from functools import lru_cache

import structlog
from openai import AsyncOpenAI

from backend.metrics import record_embedding_request
from backend.settings import Settings, get_settings

logger = structlog.get_logger()


def deterministic_embedding(text: str, *, dimensions: int | None = None) -> list[float]:
    """Build a deterministic unit vector for tests and offline development."""
    resolved_dimensions = dimensions or get_settings().semantic_memory_embedding_dim
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    seed = digest
    while len(values) < resolved_dimensions:
        for byte in seed:
            values.append((byte / 255.0) * 2.0 - 1.0)
            if len(values) >= resolved_dimensions:
                break
        seed = hashlib.sha256(seed).digest()

    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0:
        return values
    return [value / norm for value in values]


def embed_text(text: str, settings: Settings | None = None) -> list[float]:
    """Return a deterministic embedding vector (sync — for tests and offline dev)."""
    resolved = settings or get_settings()
    return deterministic_embedding(text, dimensions=resolved.semantic_memory_embedding_dim)


@lru_cache
def _embedding_client(api_key: str, base_url: str) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=api_key or "missing-key",
        base_url=base_url,
    )


async def embed_text_async(text: str, settings: Settings | None = None) -> list[float]:
    """Return an embedding vector, using OpenRouter when configured."""
    resolved = settings or get_settings()
    if resolved.embedding_provider == "deterministic":
        return deterministic_embedding(
            text,
            dimensions=resolved.semantic_memory_embedding_dim,
        )

    if not text.strip():
        msg = "Cannot embed empty text"
        raise ValueError(msg)

    start = time.perf_counter()
    client = _embedding_client(resolved.openrouter_api_key, resolved.openrouter_base_url)
    try:
        response = await client.embeddings.create(
            model=resolved.embedding_model,
            input=text,
        )
    except Exception as exc:
        record_embedding_request(
            provider=resolved.embedding_provider,
            model=resolved.embedding_model,
            status="failure",
            duration_ms=(time.perf_counter() - start) * 1000.0,
        )
        logger.warning(
            "embedding_request_failed",
            provider=resolved.embedding_provider,
            model=resolved.embedding_model,
            error=str(exc),
        )
        raise

    vector = list(response.data[0].embedding)
    if len(vector) != resolved.semantic_memory_embedding_dim:
        msg = (
            "Embedding dimension mismatch: expected "
            f"{resolved.semantic_memory_embedding_dim}, got {len(vector)}"
        )
        raise ValueError(msg)

    duration_ms = (time.perf_counter() - start) * 1000.0
    record_embedding_request(
        provider=resolved.embedding_provider,
        model=resolved.embedding_model,
        status="success",
        duration_ms=duration_ms,
    )
    return vector
