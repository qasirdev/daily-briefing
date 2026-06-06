"""Context compression for memory payloads (Gap #40)."""

from __future__ import annotations

from typing import Any

DEFAULT_MAX_CHARS = 6_000
SUMMARY_TRUNCATE = 400


def _truncate_text(value: str, limit: int) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def compress_memory_payload(
    payload: dict[str, list[dict[str, Any]]],
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> tuple[dict[str, list[dict[str, Any]]], int]:
    """Compress semantic/episodic/procedural lists to fit token budget."""
    compressed: dict[str, list[dict[str, Any]]] = {
        "semantic_memory": [],
        "procedural_skills": [],
        "episodic_lessons": [],
    }
    bytes_saved = 0

    for key in compressed:
        items = payload.get(key, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            entry = dict(item)
            for field in ("content", "summary", "name"):
                raw = entry.get(field)
                if isinstance(raw, str):
                    truncated = _truncate_text(raw, SUMMARY_TRUNCATE)
                    bytes_saved += max(0, len(raw) - len(truncated))
                    entry[field] = truncated
            compressed[key].append(entry)

    while _payload_size(compressed) > max_chars and _shrink_one(compressed):
        bytes_saved += 50

    return compressed, bytes_saved


def _payload_size(payload: dict[str, list[dict[str, Any]]]) -> int:
    total = 0
    for items in payload.values():
        for item in items:
            for value in item.values():
                if isinstance(value, str):
                    total += len(value)
                elif isinstance(value, list):
                    total += sum(len(str(v)) for v in value)
    return total


def _shrink_one(payload: dict[str, list[dict[str, Any]]]) -> bool:
    """Drop lowest-priority item: episodic → semantic → procedural."""
    for key in ("episodic_lessons", "semantic_memory", "procedural_skills"):
        items = payload.get(key, [])
        if items:
            items.pop()
            return True
    return False
