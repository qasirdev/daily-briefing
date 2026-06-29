"""Task agent LangGraph node."""

from __future__ import annotations

import time
from typing import Any, Literal

import structlog

from backend.dependencies import PostgresMCPProtocol
from backend.graph.state import BriefingGraphState
from backend.mcp.client import MCPError, MCPTimeoutError
from backend.mcp.ingress import authorize_mcp_tool, spotlight_task_rows, validate_task_response
from backend.prompt_version import resolve_prompt_version
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata
from backend.schemas.task import TaskRecord
from backend.security.abac import assert_resource_owner
from backend.security.failure_messages import failure_message_for

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
            prompt_version=resolve_prompt_version("task"),
            trace_id=state.get("trace_id", "0" * 32),
            data_classification="confidential",
            spotlighting_applied=True,
        ),
    )


async def task_agent_node(
    state: BriefingGraphState,
    postgres: PostgresMCPProtocol,
) -> dict[str, Any]:
    """Fetch and prioritize pending tasks via PostgreSQL MCP."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    user_id = state.get("user_id", "")

    logger.info("task_agent_started", trace_id=trace_id, user_id=user_id)

    assert_resource_owner(
        actor_user_id=user_id,
        resource_user_id=user_id,
        resource="tasks",
    )

    try:
        authorize_mcp_tool(
            agent_id="task_agent",
            tool="tasks.list",
            session_id=state.get("request_id", trace_id),
        )
        response = await postgres.query(sql=TASK_QUERY, user_id=user_id)
        try:
            response = validate_task_response(response)
        except ValueError as exc:
            execution_ms = int((time.perf_counter() - start) * 1000)
            logger.warning("task_agent_poisoned_response", trace_id=trace_id, error=str(exc))
            envelope = _envelope(
                status="escalated",
                state=state,
                result=None,
                execution_ms=execution_ms,
                escalation=EscalationPayload(
                    reason="security_violation_detected",
                    target_agent="dlq_handler",
                    context=str(exc)[:200],
                    retry_allowed=False,
                ),
            )
            return {
                "task_result": envelope,
                "current_agent": "task",
                "failure_reason": "security_violation_detected",
                "failure_message": failure_message_for(
                    "security_violation_detected",
                    source="task",
                ),
            }
        rows = response.get("rows", [])
        tasks: list[dict[str, object]] = []
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                parsed = TaskRecord.from_row(row)
                if parsed is not None:
                    tasks.append(parsed.model_dump())

        tasks = spotlight_task_rows(tasks)
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

    except MCPError as exc:
        execution_ms = int((time.perf_counter() - start) * 1000)
        logger.warning("task_agent_mcp_error", trace_id=trace_id, error=str(exc))
        envelope = _envelope(
            status="escalated",
            state=state,
            result=None,
            execution_ms=execution_ms,
            escalation=EscalationPayload(
                reason="unexpected_error",
                target_agent="orchestrator",
                context=str(exc),
            ),
        )
        return {"task_result": envelope, "current_agent": "task"}
