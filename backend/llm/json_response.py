"""Parse JSON payloads from LLM text responses."""

from __future__ import annotations

import json


def _strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    return stripped.removeprefix("```json").removeprefix("```").strip().removesuffix("```").strip()


def _extract_json_object(text: str) -> str:
    """Return the first balanced `{...}` object in text, or the original string."""
    start = text.find("{")
    if start < 0:
        return text

    depth = 0
    in_string = False
    escape = False
    for index, char in enumerate(text[start:], start):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return text[start:]


def parse_llm_json(content: str) -> dict[str, object]:
    """Parse JSON from an LLM response, tolerating fences and leading prose."""
    text = _strip_markdown_fence(content)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = json.loads(_extract_json_object(text))
    if not isinstance(parsed, dict):
        msg = "LLM response JSON must be an object"
        raise json.JSONDecodeError(msg, text, 0)
    return parsed
