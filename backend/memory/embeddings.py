"""Embedding helpers for semantic memory."""

from __future__ import annotations

import hashlib
import math

from backend.settings import Settings, get_settings


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
    """Return an embedding vector for semantic memory indexing."""
    resolved = settings or get_settings()
    return deterministic_embedding(text, dimensions=resolved.semantic_memory_embedding_dim)
