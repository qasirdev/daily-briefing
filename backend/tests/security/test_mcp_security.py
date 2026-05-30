"""MCP SSRF and permission security tests."""

import pytest

from backend.mcp.client import MCPPermissionError, validate_read_query
from backend.security.ssrf import SSRFValidationError, SSRFValidator


def test_ssrf_blocks_private_ip() -> None:
    validator = SSRFValidator(allowlist=("*.googleapis.com",))
    with pytest.raises(SSRFValidationError):
        validator.validate_url("http://127.0.0.1/calendar", source="test")


def test_ssrf_blocks_invalid_scheme() -> None:
    validator = SSRFValidator(allowlist=("*.googleapis.com",))
    with pytest.raises(SSRFValidationError):
        validator.validate_url("file:///etc/passwd", source="test")


def test_ssrf_allows_googleapis_host() -> None:
    validator = SSRFValidator(allowlist=("*.googleapis.com",))
    validator.validate_url("https://www.googleapis.com/calendar/v3/events", source="test")


def test_postgres_query_requires_user_id() -> None:
    with pytest.raises(MCPPermissionError):
        validate_read_query("SELECT * FROM tasks", user_id=None)


def test_postgres_query_rejects_writes() -> None:
    with pytest.raises(MCPPermissionError):
        validate_read_query("DELETE FROM tasks WHERE user_id = :user_id", user_id="user-1")
