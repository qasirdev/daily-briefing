"""Output sanitization for orchestrator-presented markdown."""

from __future__ import annotations

import nh3

from backend.logging_config import get_security_logger

ALLOWED_TAGS = frozenset(
    {
        "p",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "strong",
        "em",
        "code",
        "pre",
        "blockquote",
        "hr",
        "br",
        "a",
    },
)
ALLOWED_ATTRIBUTES: dict[str, set[str]] = {"a": {"href", "title"}}


def sanitize_markdown(content: str) -> str:
    """Sanitize HTML/markdown output before returning to clients."""
    cleaned = nh3.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
    )
    if cleaned != content:
        stripped = len(content) - len(cleaned)
        get_security_logger().info(
            "sanitization_stripped_content",
            stripped_chars=stripped,
            original_length=len(content),
        )
    return cleaned
