"""Parse JSON payloads from LLM text responses."""

from __future__ import annotations

import json


def parse_llm_json(content: str) -> dict[str, object]:
    """Parse JSON from an LLM response, stripping optional markdown fences."""
    text = content.strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").strip().removesuffix("```").strip()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        msg = "LLM response JSON must be an object"
        raise json.JSONDecodeError(msg, text, 0)
    return parsed
