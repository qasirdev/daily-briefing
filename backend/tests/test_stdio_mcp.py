"""Tests for stdio MCP helpers (no live npx subprocess)."""

import pytest

from backend.mcp.client import MCPError
from backend.mcp.stdio_transport import _content_to_dict, bind_user_id


def test_bind_user_id_replaces_placeholder() -> None:
    sql = "SELECT * FROM tasks WHERE user_id = :user_id"
    assert bind_user_id(sql, "demo-user") == "SELECT * FROM tasks WHERE user_id = 'demo-user'"


def test_bind_user_id_rejects_unsafe_user_id() -> None:
    with pytest.raises(MCPError):
        bind_user_id("SELECT 1 WHERE user_id = :user_id", "bad;drop")


def test_content_to_dict_parses_json_list() -> None:
    class Block:
        text = '[{"id": "1", "title": "Task"}]'

    result = _content_to_dict([Block()])
    assert result["row_count"] == 1
    assert result["rows"][0]["title"] == "Task"


def test_content_to_dict_parses_json_object() -> None:
    class Block:
        text = '{"events": []}'

    result = _content_to_dict([Block()])
    assert result == {"events": []}
