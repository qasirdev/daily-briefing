"""Guardrail: documented injection corpus counts stay aligned with code.

Tracked docs embed an HTML comment marker:
  <!-- corpus-inventory:payloads=N,patterns=M -->

Update the marker (and surrounding prose) whenever you change
``INJECTION_PAYLOADS`` or ``INJECTION_PATTERNS``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from backend.security.injection_patterns import INJECTION_PATTERN_COUNT, INJECTION_PATTERNS
from backend.tests.security.test_injection_payloads import (
    INJECTION_PAYLOAD_COUNT,
    INJECTION_PAYLOADS,
)

REPO_ROOT = Path(__file__).resolve().parents[3]

CORPUS_MARKER = re.compile(r"<!--\s*corpus-inventory:payloads=(\d+),patterns=(\d+)\s*-->")

TRACKED_FILES = [
    REPO_ROOT / "docs/SECURITY.md",
    REPO_ROOT / "README.md",
    REPO_ROOT / "backend/AGENT.md",
    REPO_ROOT / "007-01-ai-daily-briefing-assistant-v2.0.0.md",
]


def test_injection_payload_count_constant() -> None:
    assert INJECTION_PAYLOAD_COUNT == len(INJECTION_PAYLOADS)


def test_injection_pattern_count_constant() -> None:
    assert INJECTION_PATTERN_COUNT == len(INJECTION_PATTERNS)


@pytest.mark.parametrize("doc_path", TRACKED_FILES, ids=lambda p: p.name)
def test_corpus_inventory_markers_match_code(doc_path: Path) -> None:
    text = doc_path.read_text(encoding="utf-8")
    match = CORPUS_MARKER.search(text)
    assert match is not None, (
        f"Missing corpus-inventory marker in {doc_path.relative_to(REPO_ROOT)}. "
        "Add: <!-- corpus-inventory:payloads=N,patterns=M -->"
    )
    doc_payloads, doc_patterns = int(match.group(1)), int(match.group(2))
    assert doc_payloads == len(INJECTION_PAYLOADS), (
        f"{doc_path.name}: documented payload count {doc_payloads} != "
        f"code {len(INJECTION_PAYLOADS)}"
    )
    assert doc_patterns == len(INJECTION_PATTERNS), (
        f"{doc_path.name}: documented pattern count {doc_patterns} != "
        f"code {len(INJECTION_PATTERNS)}"
    )
