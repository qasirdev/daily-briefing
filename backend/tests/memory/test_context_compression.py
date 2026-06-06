"""Tests for memory context compression."""

from __future__ import annotations

from typing import Any

from backend.memory.context_compression import compress_memory_payload


def test_truncates_long_summaries() -> None:
    long_text = "x" * 800
    payload = {
        "semantic_memory": [{"content": long_text, "similarity": 0.9}],
        "procedural_skills": [],
        "episodic_lessons": [],
    }
    compressed, saved = compress_memory_payload(payload, max_chars=6000)
    assert len(compressed["semantic_memory"][0]["content"]) <= 400
    assert saved > 0


def test_shrinks_oversized_payload() -> None:
    payload: dict[str, list[dict[str, Any]]] = {
        "semantic_memory": [{"content": "a" * 500, "similarity": 0.9} for _ in range(20)],
        "procedural_skills": [],
        "episodic_lessons": [{"summary": "b" * 500, "lesson_type": "x"} for _ in range(20)],
    }
    compressed, _ = compress_memory_payload(payload, max_chars=1000)
    total = sum(
        len(str(v))
        for items in compressed.values()
        for item in items
        for v in item.values()
        if isinstance(v, str)
    )
    assert total <= 6000 or len(compressed["episodic_lessons"]) < 20


def test_empty_payload_unchanged() -> None:
    payload: dict[str, list[dict[str, Any]]] = {
        "semantic_memory": [],
        "procedural_skills": [],
        "episodic_lessons": [],
    }
    compressed, saved = compress_memory_payload(payload)
    assert compressed == payload
    assert saved == 0


def test_preserves_short_content() -> None:
    payload = {
        "semantic_memory": [{"content": "Short note", "similarity": 0.5}],
        "procedural_skills": [],
        "episodic_lessons": [],
    }
    compressed, saved = compress_memory_payload(payload)
    assert compressed["semantic_memory"][0]["content"] == "Short note"
    assert saved == 0
