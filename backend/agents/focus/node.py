"""Focus agent LangGraph node."""

from __future__ import annotations

import json
import time
from typing import Any

import structlog

from backend.graph.state import BriefingGraphState
from backend.llm.prompt_cache import build_llm_messages, resolve_model_name
from backend.llm.router import DataClassification, LLMError, LLMRouter
from backend.memory.audit import memory_audit_trail
from backend.memory.embeddings import embed_text_async
from backend.memory.retrieval import (
    build_focus_retrieval_query,
    retrieve_agent_memory,
)
from backend.memory.semantic import SemanticMemoryStore
from backend.memory.working import WorkingMemoryManager
from backend.preferences.store import preference_store
from backend.prompt_version import resolve_prompt_version
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata
from backend.security.token_budget import AGENT_TOKEN_BUDGETS, HARD_LIMIT_MULTIPLIER
from backend.settings import Settings, get_settings

logger = structlog.get_logger()

FOCUS_INPUT_BUDGET = AGENT_TOKEN_BUDGETS["focus"]
FOCUS_OUTPUT_BUDGET = 2_000

_default_semantic_store = SemanticMemoryStore()
_working_memory = WorkingMemoryManager()


def _normalize_focus_plan(parsed: dict[str, object]) -> dict[str, object]:
    """Unwrap LLM output when it follows the documented `{ \"plan\": {...} }` schema."""
    inner = parsed.get("plan")
    if isinstance(inner, dict):
        return inner
    return parsed


async def _persist_focus_summary(
    *,
    user_id: str,
    request_id: str,
    trace_id: str,
    plan: dict[str, object],
    store: SemanticMemoryStore,
    settings: Settings,
) -> None:
    summary = plan.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        return
    try:
        await store.store(
            user_id=user_id,
            content=summary.strip(),
            embedding=await embed_text_async(summary, settings),
            source_type="briefing",
            source_id=request_id or None,
            trace_id=trace_id,
            agent_id="focus",
        )
    except Exception as exc:
        logger.warning(
            "semantic_memory_store_failed",
            user_id=user_id,
            request_id=request_id,
            error=str(exc),
        )


async def focus_agent_node(
    state: BriefingGraphState,
    llm: LLMRouter,
    semantic_store: SemanticMemoryStore | None = None,
) -> dict[str, Any]:
    """Generate a structured daily focus plan using the LLM router."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    request_id = state.get("request_id", "")
    settings = get_settings()
    store = semantic_store or _default_semantic_store

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

    user_id = state.get("user_id", "")
    preferences = preference_store.top_context_snippets(user_id)
    working_context = state.get("working_memory_context", [])
    normalized_working = (
        [str(item) for item in working_context] if isinstance(working_context, list) else []
    )

    if normalized_working:
        memory_audit_trail.log_read(
            trace_id=trace_id,
            request_id=request_id,
            user_id=user_id or "anonymous",
            agent_id="focus",
            memory_layer="working",
            operation="snapshot",
            result_count=len(normalized_working),
            query_summary="working_memory_context",
        )

    retrieval_query = build_focus_retrieval_query(
        tasks=tasks,
        events=events,
        working_context=normalized_working,
    )
    memory_context = await retrieve_agent_memory(
        user_id=user_id,
        agent_id="focus",
        trace_id=trace_id,
        request_id=request_id,
        query_text=retrieval_query,
        working_context=normalized_working,
        tasks=tasks,
        events=events,
        settings=settings,
        has_prior_briefings=bool(preferences),
        compress_payload=True,
    )
    memory_payload = memory_context.to_payload(
        compress=True,
        max_chars=settings.context_compression_max_chars,
    )

    user_context = json.dumps(
        {
            "tasks": tasks,
            "events": events,
            "preferences": preferences,
            **memory_payload,
        },
        ensure_ascii=True,
    )
    user_content = (
        "<user_data>\n"
        f"{user_context}\n"
        "</user_data>\n"
        "Create a JSON plan with time_blocks including task references."
    )
    messages = build_llm_messages(
        "focus",
        user_content,
        model=resolve_model_name(llm),
        enable_caching=settings.enable_prompt_caching,
    )

    estimated_input = sum(len(m.get("content", "")) for m in messages) // 4
    focus_hard_limit = FOCUS_INPUT_BUDGET * HARD_LIMIT_MULTIPLIER
    if estimated_input > focus_hard_limit:
        execution_ms = int((time.perf_counter() - start) * 1000)
        envelope = AgentResultEnvelope(
            agent_id="focus",
            canonical_role="planner",
            status="escalated",
            escalation=EscalationPayload(
                reason="token_budget_exceeded",
                target_agent="orchestrator",
                context=(
                    f"Focus agent input estimate {estimated_input} exceeds "
                    f"hard limit {focus_hard_limit}"
                ),
            ),
            metadata=ExecutionMetadata(
                execution_ms=execution_ms,
                tokens_used=0,
                model_used="none",
                prompt_version=resolve_prompt_version("focus"),
                trace_id=trace_id,
                data_classification="internal",
            ),
        )
        return {"focus_result": envelope, "current_agent": "focus"}

    has_pii = bool(tasks or events)
    data_classification: DataClassification = "confidential_pii" if has_pii else "confidential"

    try:
        llm_response = await llm.generate(
            messages=messages,
            trace_id=trace_id,
            input_budget=FOCUS_INPUT_BUDGET,
            output_budget=FOCUS_OUTPUT_BUDGET,
            data_classification=data_classification,
            agent_id="focus",
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
                prompt_version=resolve_prompt_version("focus"),
                trace_id=trace_id,
                data_classification="internal",
            ),
        )
        return {"focus_result": envelope, "current_agent": "focus"}

    try:
        plan = json.loads(llm_response.content)
    except json.JSONDecodeError:
        text = llm_response.content.strip()
        if text.startswith("```"):
            text = (
                text.removeprefix("```json").removeprefix("```").strip().removesuffix("```").strip()
            )
        try:
            plan = json.loads(text)
        except json.JSONDecodeError:
            plan = {"time_blocks": [], "summary": "Focus plan could not be parsed. Please retry."}

    if isinstance(plan, dict):
        plan = _normalize_focus_plan(plan)

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
            prompt_version=resolve_prompt_version("focus"),
            trace_id=trace_id,
            data_classification="confidential",
        ),
    )

    if user_id:
        await _persist_focus_summary(
            user_id=user_id,
            request_id=request_id,
            trace_id=trace_id,
            plan=plan,
            store=store,
            settings=settings,
        )

    summary_snippet = plan.get("summary")
    context_snippet = str(summary_snippet) if isinstance(summary_snippet, str) else None
    working_update = _working_memory.record_agent_turn(
        state,
        agent_id="focus",
        tokens_used=llm_response.tokens_used,
        context_snippet=context_snippet,
    )

    session_tokens = state.get("total_tokens", 0)
    return {
        "focus_result": envelope,
        "current_agent": "focus",
        "total_tokens": session_tokens + llm_response.tokens_used,
        **working_update,
    }
