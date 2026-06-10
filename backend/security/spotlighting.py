"""Spotlighting markers for untrusted external content (Gap #114)."""

from __future__ import annotations

EXTERNAL_CONTENT_OPEN = "<<<EXTERNAL_CONTENT>>>"
EXTERNAL_CONTENT_CLOSE = "<<</EXTERNAL_CONTENT>>>"


def is_spotlighted(content: str) -> bool:
    """Return True when content is already wrapped in spotlight markers."""
    return EXTERNAL_CONTENT_OPEN in content and EXTERNAL_CONTENT_CLOSE in content


def spotlight_external_content(content: str) -> str:
    """Wrap external content in spotlighting markers for LLM data-only treatment."""
    if not content.strip():
        return content
    if is_spotlighted(content):
        return content
    return f"{EXTERNAL_CONTENT_OPEN}\n{content}\n{EXTERNAL_CONTENT_CLOSE}"


def extract_spotlighted_content(content: str) -> str:
    """Return inner payload from spotlight markers, or the original string."""
    if not is_spotlighted(content):
        return content
    inner = content.split(EXTERNAL_CONTENT_OPEN, 1)[1]
    return inner.rsplit(EXTERNAL_CONTENT_CLOSE, 1)[0].strip("\n")
