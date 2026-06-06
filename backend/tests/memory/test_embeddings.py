"""Tests for semantic memory embeddings."""

import math

from backend.memory.embeddings import deterministic_embedding, embed_text
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
