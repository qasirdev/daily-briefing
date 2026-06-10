"""Tests for LLM JSON response parsing."""

import json

import pytest

from backend.llm.json_response import parse_llm_json


def test_parse_llm_json_accepts_plain_object() -> None:
    payload = {"plan": {"summary": "Focus on interviews", "time_blocks": []}}
    assert parse_llm_json(json.dumps(payload)) == payload


def test_parse_llm_json_strips_markdown_fence() -> None:
    payload = {"approved": True, "issues": []}
    wrapped = f"```json\n{json.dumps(payload)}\n```"
    assert parse_llm_json(wrapped) == payload


def test_parse_llm_json_extracts_object_from_preamble() -> None:
    payload = {"plan": {"summary": "Ship the feature", "time_blocks": []}}
    text = f"Here is the plan:\n{json.dumps(payload)}\nThanks."
    assert parse_llm_json(text) == payload


def test_parse_llm_json_rejects_non_object() -> None:
    with pytest.raises(json.JSONDecodeError):
        parse_llm_json("[1, 2, 3]")
