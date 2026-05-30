"""Focus agent LangGraph node."""

from __future__ import annotations

import json
import time
from typing import Any

import structlog

from backend.graph.state import BriefingGraphState
from backend.llm.router import LLMError, LLMRouter
from backend.prompts_loader import build_agent_system_prompt
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata

logger = structlog.get_logger()

FOCUS_INPUT_BUDGET = 8_000
FOCUS_OUTPUT_BUDGET = 2_000


async def focus_agent_node(
    state: BriefingGraphState,
    llm: LLMRouter,
) -> dict[str, Any]:
    """Generate a structured daily focus plan using the LLM router."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)

    tasks: list[dict[str, object]] = []
    events: list[dict[str, object]] = []
    task_result = state.get("task_result")
    calendar_result = state.get("calendar_result")
    if isinstance(task_result, AgentResultEnvelope) and task_result.result:
        raw_tasks = task_result.result.get("tasks", [])
        if isinstance(raw_tasks, list):
            tasks = [item for item in raw_tasks if isinstance(item, dict)]
    if isinstance(calendar_result, AgentResultEnvelope) and calendar_result.result:
        raw_events = calendar_result.result.get("events", [])
        if isinstance(raw_events, list):
            events = [item for item in raw_events if isinstance(item, dict)]

    user_context = json.dumps({"tasks": tasks, "events": events}, ensure_ascii=True)
    system_prompt = build_agent_system_prompt("focus")
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                "<user_data>\n"
                f"{user_context}\n"
                "</user_data>\n"
                "Create a JSON plan with time_blocks including task references."
            ),
        },
    ]

    total_tokens = state.get("total_tokens", 0)
    if total_tokens > FOCUS_INPUT_BUDGET * 2:
        execution_ms = int((time.perf_counter() - start) * 1000)
        envelope = AgentResultEnvelope(
            agent_id="focus",
            canonical_role="planner",
            status="escalated",
            escalation=EscalationPayload(
                reason="token_budget_exceeded",
                target_agent="orchestrator",
                context="Focus agent exceeded 2x token budget",
            ),
            metadata=ExecutionMetadata(
                execution_ms=execution_ms,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id=trace_id,
                data_classification="internal",
            ),
        )
        return {"focus_result": envelope, "current_agent": "focus"}

    try:
        llm_response = await llm.generate(
            messages=messages,
            trace_id=trace_id,
            input_budget=FOCUS_INPUT_BUDGET,
            output_budget=FOCUS_OUTPUT_BUDGET,
        )
    except LLMError as exc:
        execution_ms = int((time.perf_counter() - start) * 1000)
        envelope = AgentResultEnvelope(
            agent_id="focus",
            canonical_role="planner",
            status="escalated",
            escalation=EscalationPayload(
                reason="unexpected_error",
                target_agent="orchestrator",
                context=str(exc),
            ),
            metadata=ExecutionMetadata(
                execution_ms=execution_ms,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id=trace_id,
                data_classification="internal",
            ),
        )
        return {"focus_result": envelope, "current_agent": "focus"}

    try:
        plan = json.loads(llm_response.content)
    except json.JSONDecodeError:
        plan = {
            "time_blocks": [],
            "summary": llm_response.content,
        }

    if not tasks and not events:
        plan = {"time_blocks": [], "summary": "Minimal plan — no tasks or events available."}

    execution_ms = int((time.perf_counter() - start) * 1000)
    envelope = AgentResultEnvelope(
        agent_id="focus",
        canonical_role="planner",
        status="success",
        result={"plan": plan},
        metadata=ExecutionMetadata(
            execution_ms=execution_ms,
            tokens_used=llm_response.tokens_used,
            model_used=llm_response.model_used,
            prompt_version="v1.5.0",
            trace_id=trace_id,
            data_classification="confidential",
        ),
    )
    return {
        "focus_result": envelope,
        "current_agent": "focus",
        "total_tokens": total_tokens + llm_response.tokens_used,
    }
