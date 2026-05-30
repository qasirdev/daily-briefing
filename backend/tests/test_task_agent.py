"""Task agent unit tests."""

import pytest

from backend.agents.task.node import task_agent_node
from backend.graph.state import BriefingGraphState
from backend.mcp.client import MCPError, MCPTimeoutError
from backend.mcp.postgres import PostgresMCPClient


class FakePostgres(PostgresMCPClient):
    def __init__(
        self,
        rows: list[dict[str, object]] | None = None,
        timeout: bool = False,
    ) -> None:
        super().__init__(host="localhost", port=5433)
        self._rows = rows or []
        self._timeout = timeout

    async def query(
        self,
        *,
        sql: str,
        user_id: str,
        params: dict[str, object] | None = None,
    ) -> dict[str, object]:
        if self._timeout:
            raise MCPTimeoutError("timeout")
        return {"rows": self._rows}


@pytest.mark.asyncio
async def test_task_agent_sorts_by_priority() -> None:
    state: BriefingGraphState = {"user_id": "u1", "trace_id": "a" * 32}
    low_task = {
        "id": "1",
        "title": "Low",
        "priority": "low",
        "due_date": "2026-05-30",
        "status": "pending",
    }
    high_task = {
        "id": "2",
        "title": "High",
        "priority": "high",
        "due_date": "2026-05-31",
        "status": "pending",
    }
    postgres = FakePostgres([dict(low_task), dict(high_task)])
    result = await task_agent_node(state, postgres)
    envelope = result["task_result"]
    assert envelope is not None
    assert envelope.status == "success"
    assert envelope.result is not None
    tasks = envelope.result["tasks"]
    assert isinstance(tasks, list)
    assert tasks[0]["priority"] == "high"


@pytest.mark.asyncio
async def test_task_agent_escalates_on_mcp_connection_error() -> None:
    state: BriefingGraphState = {"user_id": "u1", "trace_id": "c" * 32}

    class FailingPostgres(FakePostgres):
        async def query(
            self,
            *,
            sql: str,
            user_id: str,
            params: dict[str, object] | None = None,
        ) -> dict[str, object]:
            raise MCPError("MCP transport error for 'query': All connection attempts failed")

    result = await task_agent_node(state, FailingPostgres())
    envelope = result["task_result"]
    assert envelope is not None
    assert envelope.status == "escalated"
    assert envelope.escalation is not None
    assert envelope.escalation.reason == "unexpected_error"


@pytest.mark.asyncio
async def test_task_agent_escalates_on_timeout() -> None:
    state: BriefingGraphState = {"user_id": "u1", "trace_id": "b" * 32}
    postgres = FakePostgres(timeout=True)
    result = await task_agent_node(state, postgres)
    envelope = result["task_result"]
    assert envelope is not None
    assert envelope.status == "escalated"
    assert envelope.escalation is not None
    assert envelope.escalation.reason == "mcp_timeout"
