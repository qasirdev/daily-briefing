"""Verification agent LangGraph node."""

from __future__ import annotations

import json
import time
from typing import Any, Literal

import structlog

from backend.graph.state import BriefingGraphState
from backend.llm.json_response import parse_llm_json
from backend.llm.models import LLMResponse
from backend.llm.prompt_cache import build_llm_messages, resolve_model_name
from backend.llm.router import LLMError, LLMRouter
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata
from backend.settings import get_settings

logger = structlog.get_logger()

PROMPT_VERSION = "v1.1.0"
VERIFICATION_INPUT_BUDGET = 12_000
VERIFICATION_OUTPUT_BUDGET = 2_000


def _build_envelope(
    *,
    state: BriefingGraphState,
    status: Literal["success", "failure", "escalated"],
    result: dict[str, object],
    execution_ms: int,
    escalation: EscalationPayload | None = None,
    llm_response: LLMResponse | None = None,
) -> AgentResultEnvelope:
    trace_id = state.get("trace_id", "0" * 32)
    return AgentResultEnvelope(
        agent_id="verification",
        canonical_role="verifier",
        status=status,
        result=result,
        escalation=escalation,
        metadata=ExecutionMetadata(
            execution_ms=execution_ms,
            tokens_used=llm_response.tokens_used if llm_response else 0,
            model_used=llm_response.model_used if llm_response else "none",
            prompt_version=PROMPT_VERSION,
            trace_id=trace_id,
            data_classification="internal",
        ),
    )


def _serialize_envelope_result(envelope: AgentResultEnvelope | None) -> dict[str, object] | None:
    if envelope is None or envelope.result is None:
        return None
    return dict(envelope.result)


def _build_verification_user_content(state: BriefingGraphState) -> str:
    task = state.get("task_result")
    calendar = state.get("calendar_result")
    focus = state.get("focus_result")
    payload = {
        "task_mcp_response": _serialize_envelope_result(
            task if isinstance(task, AgentResultEnvelope) else None,
        ),
        "calendar_mcp_response": _serialize_envelope_result(
            calendar if isinstance(calendar, AgentResultEnvelope) else None,
        ),
        "focus_agent_output": _serialize_envelope_result(
            focus if isinstance(focus, AgentResultEnvelope) else None,
        ),
    }
    return (
        "Verify the focus plan against raw MCP source data. "
        "Return ONLY JSON matching output-schema.md.\n\n"
        "<source_data>\n"
        f"{json.dumps(payload, ensure_ascii=True)}\n"
        "</source_data>"
    )


def _verify_focus_against_sources(state: BriefingGraphState) -> dict[str, object]:
    """Heuristic fact-check of focus plan against task and calendar MCP data."""
    flagged_claims: list[dict[str, object]] = []
    verified_claims: list[str] = []

    focus = state.get("focus_result")
    calendar = state.get("calendar_result")
    task = state.get("task_result")

    if not isinstance(focus, AgentResultEnvelope) or focus.result is None:
        return {
            "status": "discrepancies_found",
            "verified_claims": [],
            "flagged_claims": [
                {
                    "claim": "focus plan present",
                    "issue": "Focus agent produced no output to verify",
                    "source_truth": "focus_result is empty",
                    "severity": "critical",
                },
            ],
            "confidence": 0.0,
        }

    plan = focus.result.get("plan")
    if not isinstance(plan, dict):
        return {
            "status": "discrepancies_found",
            "verified_claims": [],
            "flagged_claims": [
                {
                    "claim": "structured focus plan",
                    "issue": "Focus output is not a structured plan",
                    "source_truth": "plan field missing or invalid",
                    "severity": "major",
                },
            ],
            "confidence": 0.3,
        }

    events: list[dict[str, object]] = []
    if isinstance(calendar, AgentResultEnvelope) and calendar.result:
        raw_events = calendar.result.get("events", [])
        if isinstance(raw_events, list):
            events = [item for item in raw_events if isinstance(item, dict)]

    tasks: list[dict[str, object]] = []
    if isinstance(task, AgentResultEnvelope) and task.result:
        raw_tasks = task.result.get("tasks", [])
        if isinstance(raw_tasks, list):
            tasks = [item for item in raw_tasks if isinstance(item, dict)]

    if events:
        verified_claims.append(f"{len(events)} calendar event(s) available for cross-check")
    if tasks:
        verified_claims.append(f"{len(tasks)} task(s) available for cross-check")

    blocks = plan.get("time_blocks")
    if isinstance(blocks, list) and events and len(blocks) > len(events) * 3:
        flagged_claims.append(
            {
                "claim": "time block count vs calendar density",
                "issue": "Focus plan has many blocks relative to calendar events",
                "source_truth": json.dumps({"events": len(events), "blocks": len(blocks)}),
                "severity": "minor",
            },
        )

    has_critical = any(
        isinstance(item, dict) and item.get("severity") == "critical" for item in flagged_claims
    )
    has_major = any(
        isinstance(item, dict) and item.get("severity") == "major" for item in flagged_claims
    )

    if has_critical or has_major:
        status = "discrepancies_found"
        confidence = 0.4
    elif flagged_claims:
        status = "verified"
        confidence = 0.85
    else:
        status = "verified"
        confidence = 1.0

    return {
        "status": status,
        "verified_claims": verified_claims,
        "flagged_claims": flagged_claims,
        "confidence": confidence,
    }


async def _llm_verify(
    state: BriefingGraphState,
    llm: LLMRouter,
    *,
    trace_id: str,
) -> tuple[dict[str, object], LLMResponse | None]:
    settings = get_settings()
    messages = build_llm_messages(
        "verification",
        _build_verification_user_content(state),
        model=resolve_model_name(llm),
        enable_caching=settings.enable_prompt_caching,
    )
    try:
        response = await llm.generate(
            messages=messages,
            trace_id=trace_id,
            input_budget=VERIFICATION_INPUT_BUDGET,
            output_budget=VERIFICATION_OUTPUT_BUDGET,
            agent_id="verification",
            data_classification="confidential",
        )
        verification = parse_llm_json(response.content)
    except (LLMError, json.JSONDecodeError) as exc:
        logger.warning("verification_llm_fallback", trace_id=trace_id, error=str(exc))
        return _verify_focus_against_sources(state), None

    for key in ("status", "verified_claims", "flagged_claims", "confidence"):
        if key not in verification:
            return _verify_focus_against_sources(state), response

    return verification, response


def _envelope_from_verification(
    *,
    state: BriefingGraphState,
    verification: dict[str, object],
    execution_ms: int,
    llm_response: LLMResponse | None,
) -> AgentResultEnvelope:
    if verification.get("status") == "discrepancies_found":
        flagged_raw = verification.get("flagged_claims", [])
        flagged_list = flagged_raw if isinstance(flagged_raw, list) else []
        critical_count = sum(
            1
            for item in flagged_list
            if isinstance(item, dict) and item.get("severity") in {"critical", "major"}
        )
        return _build_envelope(
            state=state,
            status="escalated" if critical_count > 0 else "success",
            result=verification,
            execution_ms=execution_ms,
            escalation=(
                EscalationPayload(
                    reason="unexpected_error",
                    target_agent="orchestrator",
                    context=f"Verification found {critical_count} major/critical discrepancies",
                )
                if critical_count > 0
                else None
            ),
            llm_response=llm_response,
        )

    return _build_envelope(
        state=state,
        status="success",
        result=verification,
        execution_ms=execution_ms,
        llm_response=llm_response,
    )


async def verification_agent_node(
    state: BriefingGraphState,
    llm: LLMRouter | None = None,
) -> dict[str, Any]:
    """Verify focus output against MCP source data via LLM with heuristic fallback."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    logger.info("verification_agent_started", trace_id=trace_id)

    llm_response: LLMResponse | None = None
    if llm is not None:
        verification, llm_response = await _llm_verify(state, llm, trace_id=trace_id)
    else:
        verification = _verify_focus_against_sources(state)

    execution_ms = int((time.perf_counter() - start) * 1000)
    envelope = _envelope_from_verification(
        state=state,
        verification=verification,
        execution_ms=execution_ms,
        llm_response=llm_response,
    )

    update: dict[str, Any] = {
        "verification_result": envelope,
        "current_agent": "verification",
    }
    if llm_response is not None:
        update["total_tokens"] = state.get("total_tokens", 0) + llm_response.tokens_used

    return update
