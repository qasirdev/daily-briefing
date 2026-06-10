"""Guardrail: documented pytest collection counts stay aligned with the suite.

Tracked docs embed an HTML comment marker:
  <!-- test-inventory:total=N -->

Update the marker (and surrounding prose) whenever you add or remove tests.
"""

from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

SUITE_MARKER = re.compile(r"<!--\s*test-inventory:total=(\d+)\s*-->")

TRACKED_FILES = [
    REPO_ROOT / "docs/SECURITY.md",
    REPO_ROOT / "README.md",
    REPO_ROOT / "backend/AGENT.md",
    REPO_ROOT / "007-01-ai-daily-briefing-assistant-v2.0.0.md",
    REPO_ROOT / "AGENT.md",
]


@lru_cache(maxsize=1)
def pytest_collection_count() -> int:
    result = subprocess.run(
        ["uv", "run", "pytest", "--collect-only", "-q", "backend/tests"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"pytest collection failed — fix collection errors before updating docs:\n{result.stderr}"
    )
    combined = result.stdout + result.stderr
    match = re.search(r"(\d+)\s+tests?\s+collected", combined)
    assert match is not None, f"Could not parse pytest collection output:\n{combined}"
    return int(match.group(1))


@pytest.mark.parametrize("doc_path", TRACKED_FILES, ids=lambda p: p.name)
def test_suite_inventory_markers_match_code(doc_path: Path) -> None:
    expected = pytest_collection_count()
    text = doc_path.read_text(encoding="utf-8")
    match = SUITE_MARKER.search(text)
    assert match is not None, (
        f"Missing test-inventory marker in {doc_path.relative_to(REPO_ROOT)}. "
        "Add: <!-- test-inventory:total=N -->"
    )
    doc_total = int(match.group(1))
    assert doc_total == expected, (
        f"{doc_path.name}: documented total {doc_total} != "
        f"pytest collection {expected}. "
        "Update the marker and any prose citing the total test count."
    )
