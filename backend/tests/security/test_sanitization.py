"""Output sanitization security tests."""

from backend.security.sanitization import sanitize_markdown


def test_script_tags_stripped() -> None:
    dirty = '<script>alert("xss")</script><p>Hello</p>'
    cleaned = sanitize_markdown(dirty)
    assert "<script>" not in cleaned
    assert "Hello" in cleaned


def test_allowed_tags_preserved() -> None:
    html = "<h1>Title</h1><ul><li>Item</li></ul><strong>Bold</strong>"
    cleaned = sanitize_markdown(html)
    assert "<h1>" in cleaned
    assert "<li>" in cleaned
    assert "<strong>" in cleaned


def test_event_handlers_removed() -> None:
    dirty = '<p onclick="steal()">Click</p>'
    cleaned = sanitize_markdown(dirty)
    assert "onclick" not in cleaned
