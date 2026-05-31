"""Live integration tests for Option 1 stdio MCP (requires .env secrets)."""

from __future__ import annotations

import os
import time

import pytest

from backend.agents.task.node import task_agent_node
from backend.graph.state import BriefingGraphState
from backend.mcp.postgres_stdio import PostgresMCPStdioClient
from backend.schemas.envelope import AgentResultEnvelope

pytestmark = pytest.mark.skipif(
    os.getenv("LIVE_STDIO_E2E") != "1",
    reason="Set LIVE_STDIO_E2E=1 with Supabase configured",
)


@pytest.mark.asyncio
async def test_live_stdio_postgres_query() -> None:
    """PostgreSQL MCP stdio returns task rows from Supabase."""
    client = PostgresMCPStdioClient()
    sql = """
SELECT id, title, priority, due_date, status
FROM tasks
WHERE user_id = :user_id AND status = 'pending'
LIMIT 5
"""
    result = await client.query(sql=sql, user_id="demo-user")
    assert isinstance(result.get("rows"), list)


@pytest.mark.asyncio
async def test_live_stdio_task_agent_node() -> None:
    """Task agent node succeeds against Supabase via stdio MCP."""
    postgres = PostgresMCPStdioClient()
    state: BriefingGraphState = {
        "user_id": "demo-user",
        "trace_id": "c" * 32,
        "graph_started_at": time.perf_counter(),
    }
    update = await task_agent_node(state, postgres)
    envelope = update.get("task_result")
    assert isinstance(envelope, AgentResultEnvelope)
    assert envelope.status == "success"
    assert envelope.result is not None
    assert isinstance(envelope.result.get("tasks"), list)
