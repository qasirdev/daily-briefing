"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterator, MutableMapping
from contextlib import contextmanager
from typing import Any
from uuid import uuid4

import structlog

from backend.security.pii import mask_pii

MAX_LOG_PAYLOAD = 2_000
_LOG_PII_SKIP_KEYS = frozenset({"trace_id", "request_id", "span_id"})


def _mask_pii(
    _logger: Any,
    _method: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    for key, value in list(event_dict.items()):
        if key in _LOG_PII_SKIP_KEYS:
            continue
        if isinstance(value, str):
            masked = mask_pii(value)
            if len(masked) > MAX_LOG_PAYLOAD:
                masked = masked[:MAX_LOG_PAYLOAD] + "...[truncated]"
            event_dict[key] = masked
    return event_dict


def _ensure_trace_id(
    _logger: Any,
    _method: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    if "trace_id" not in event_dict:
        event_dict["trace_id"] = uuid4().hex
        event_dict["trace_id_generated"] = True
    return event_dict


def configure_logging(*, debug: bool = False) -> None:
    """Configure structlog for JSON output with trace_id support."""
    log_level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _ensure_trace_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            _mask_pii,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def bind_trace_id(trace_id: str) -> None:
    """Bind trace_id to the current structlog context."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(trace_id=trace_id)


def get_logger(name: str | None = None) -> Any:
    """Return a structlog logger."""
    return structlog.get_logger(name)


def get_security_logger() -> Any:
    """Return the security audit logger."""
    return structlog.get_logger("security")


@contextmanager
def agent_log_context(*, trace_id: str, agent_id: str) -> Iterator[None]:
    """Bind agent execution context for structured logs."""
    structlog.contextvars.bind_contextvars(trace_id=trace_id, agent_id=agent_id)
    try:
        yield
    finally:
        structlog.contextvars.unbind_contextvars("agent_id")
