"""Tests for episodic privilege sanitization (Gap #119)."""

from __future__ import annotations

import pytest

from backend.memory.privilege import sanitize_lesson_content


@pytest.mark.parametrize(
    ("content", "forbidden"),
    [
        ("User has admin access to all systems", "admin access"),
        ("Stored api_key=super-secret-value in notes", "api_key="),
        ("Bearer token=abc123def456 was used", "token=abc"),
        ("Password: hunter2 for the portal", "Password:"),
    ],
)
def test_sanitize_lesson_content_redacts_privilege_patterns(
    content: str,
    forbidden: str,
) -> None:
    sanitized = sanitize_lesson_content(content)
    assert forbidden.lower() not in sanitized.lower()
    assert "[REDACTED]" in sanitized


def test_sanitize_lesson_content_preserves_safe_lessons() -> None:
    content = "User granted calendar access for session abc123 at 09:00."
    assert sanitize_lesson_content(content) == content


def test_sanitize_lesson_content_returns_empty_for_blank_input() -> None:
    assert sanitize_lesson_content("   ") == ""
