"""Tests for structured logging."""

import json

import pytest
import structlog

from backend.logging_config import configure_logging, get_logger


def test_logs_include_trace_id(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(debug=True)
    logger = get_logger("test")
    structlog.contextvars.bind_contextvars(trace_id="1" * 32)
    logger.info("test_event", detail="hello")
    captured = capsys.readouterr().out.strip()
    payload = json.loads(captured)
    assert payload["trace_id"] == "1" * 32
    assert payload["event"] == "test_event"


def test_pii_masked_in_logs(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(debug=True)
    logger = get_logger("test")
    structlog.contextvars.bind_contextvars(trace_id="2" * 32)
    logger.info("contact", email="user@example.com", phone="555-123-4567")
    captured = capsys.readouterr().out.strip()
    payload = json.loads(captured)
    assert "[REDACTED_EMAIL]" in payload["email"]
    assert "[REDACTED_PHONE]" in payload["phone"]
