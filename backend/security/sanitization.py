"""Output sanitization for orchestrator-presented markdown."""

import nh3


def sanitize_markdown(content: str) -> str:
    """Sanitize HTML/markdown output before returning to clients."""
    return nh3.clean(
        content,
        tags={
            "p",
            "h1",
            "h2",
            "h3",
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
        attributes={"a": {"href", "title"}},
    )
