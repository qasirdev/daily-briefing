"""Task agent LangGraph node."""

from __future__ import annotations

import time
from typing import Any, Literal

import structlog

from backend.graph.state import BriefingGraphState
from backend.mcp.client import MCPTimeoutError
from backend.mcp.postgres import PostgresMCPClient
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata
from backend.schemas.task import TaskRecord

logger = structlog.get_logger()

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

TASK_QUERY = """
SELECT id, title, priority, due_date, status
FROM tasks
WHERE user_id = :user_id AND status = 'pending'
ORDER BY priority DESC, due_date ASC
LIMIT 20
"""


def _envelope(
    *,
    status: Literal["success", "failure", "escalated"],
    state: BriefingGraphState,
    result: dict[str, object] | None,
    execution_ms: int,
    tokens_used: int = 0,
    escalation: EscalationPayload | None = None,
) -> AgentResultEnvelope:
    return AgentResultEnvelope(
        agent_id="task",
        canonical_role="doer",
        status=status,
        result=result,
        escalation=escalation,
        metadata=ExecutionMetadata(
            execution_ms=execution_ms,
            tokens_used=tokens_used,
            model_used="none",
            prompt_version="v1.5.0",
            trace_id=state.get("trace_id", "0" * 32),
            data_classification="confidential",
        ),
    )


async def task_agent_node(
    state: BriefingGraphState,
    postgres: PostgresMCPClient,
) -> dict[str, Any]:
    """Fetch and prioritize pending tasks via PostgreSQL MCP."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    user_id = state.get("user_id", "")

    logger.info("task_agent_started", trace_id=trace_id, user_id=user_id)

    try:
        response = await postgres.query(sql=TASK_QUERY, user_id=user_id)
        rows = response.get("rows", [])
        tasks: list[dict[str, object]] = []
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                parsed = TaskRecord.from_row(row)
                if parsed is not None:
                    tasks.append(parsed.model_dump())

        tasks.sort(
            key=lambda item: (
                PRIORITY_ORDER.get(str(item.get("priority", "medium")), 1),
                str(item.get("due_date") or "9999-12-31"),
            ),
        )

        execution_ms = int((time.perf_counter() - start) * 1000)
        envelope = _envelope(
            status="success",
            state=state,
            result={"tasks": tasks},
            execution_ms=execution_ms,
        )
        return {"task_result": envelope, "current_agent": "task"}

    except MCPTimeoutError:
        execution_ms = int((time.perf_counter() - start) * 1000)
        envelope = _envelope(
            status="escalated",
            state=state,
            result=None,
            execution_ms=execution_ms,
            escalation=EscalationPayload(
                reason="mcp_timeout",
                target_agent="orchestrator",
                context="PostgreSQL MCP query exceeded 30s timeout",
            ),
        )
        return {"task_result": envelope, "current_agent": "task"}
