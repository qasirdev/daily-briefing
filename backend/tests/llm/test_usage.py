"""Tests for LLM usage and cost extraction."""

from __future__ import annotations

from types import SimpleNamespace

from backend.llm.usage import (
    extract_completion_tokens,
    extract_cost_usd,
    extract_prompt_tokens,
)


def test_extract_cost_usd_from_attribute() -> None:
    usage = SimpleNamespace(cost=0.00084, prompt_tokens=100, completion_tokens=50)
    assert extract_cost_usd(usage) == 0.00084


def test_extract_cost_usd_from_model_dump() -> None:
    class Usage:
        def model_dump(self) -> dict[str, float]:
            return {"cost": 0.0012}

    assert extract_cost_usd(Usage()) == 0.0012


def test_extract_token_counts() -> None:
    usage = SimpleNamespace(prompt_tokens=1200, completion_tokens=340, total_tokens=1540)
    assert extract_prompt_tokens(usage) == 1200
    assert extract_completion_tokens(usage) == 340
