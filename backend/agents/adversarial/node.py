"""Adversarial agent LangGraph node."""

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
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.settings import get_settings

logger = structlog.get_logger()

PROMPT_VERSION = "v1.1.0"
ADVERSARIAL_INPUT_BUDGET = 14_000
ADVERSARIAL_OUTPUT_BUDGET = 2_500


def _build_envelope(
    *,
    state: BriefingGraphState,
    result: dict[str, object],
    execution_ms: int,
    llm_response: LLMResponse | None = None,
) -> AgentResultEnvelope:
    trace_id = state.get("trace_id", "0" * 32)
    return AgentResultEnvelope(
        agent_id="adversarial",
        canonical_role="adversarial",
        status="success",
        result=result,
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


def _build_adversarial_user_content(state: BriefingGraphState) -> str:
    verification = state.get("verification_result")
    focus = state.get("focus_result")
    task = state.get("task_result")
    calendar = state.get("calendar_result")
    payload = {
        "verification_result": _serialize_envelope_result(
            verification if isinstance(verification, AgentResultEnvelope) else None,
        ),
        "focus_agent_output": _serialize_envelope_result(
            focus if isinstance(focus, AgentResultEnvelope) else None,
        ),
        "task_mcp_response": _serialize_envelope_result(
            task if isinstance(task, AgentResultEnvelope) else None,
        ),
        "calendar_mcp_response": _serialize_envelope_result(
            calendar if isinstance(calendar, AgentResultEnvelope) else None,
        ),
    }
    return (
        "Challenge the verification output and focus plan from a red-team perspective. "
        "Return ONLY JSON matching output-schema.md.\n\n"
        "<review_data>\n"
        f"{json.dumps(payload, ensure_ascii=True)}\n"
        "</review_data>"
    )


def _review_outputs(state: BriefingGraphState) -> dict[str, object]:
    """Heuristic red-team review of verification and focus outputs."""
    challenges: list[dict[str, object]] = []
    verification = state.get("verification_result")

    if isinstance(verification, AgentResultEnvelope) and verification.result:
        flagged = verification.result.get("flagged_claims", [])
        if isinstance(flagged, list):
            for item in flagged:
                if not isinstance(item, dict):
                    continue
                severity = item.get("severity")
                challenge_severity: Literal["minor", "moderate", "severe"]
                if severity == "critical":
                    challenge_severity = "severe"
                elif severity == "major":
                    challenge_severity = "moderate"
                else:
                    challenge_severity = "minor"
                challenges.append(
                    {
                        "target": str(item.get("claim", "focus claim")),
                        "concern": str(item.get("issue", "Potential factual mismatch")),
                        "alternative": str(item.get("source_truth", "Reconcile with MCP data")),
                        "severity": challenge_severity,
                    },
                )

    severe_count = sum(
        1 for item in challenges if isinstance(item, dict) and item.get("severity") == "severe"
    )
    moderate_count = sum(
        1 for item in challenges if isinstance(item, dict) and item.get("severity") == "moderate"
    )

    if severe_count >= 2:
        risk_level: Literal["low", "medium", "high"] = "high"
        recommended_action: Literal["approve", "request_clarification", "reject"] = "reject"
    elif severe_count >= 1 or moderate_count >= 1:
        risk_level = "medium"
        recommended_action = "request_clarification"
    else:
        risk_level = "low"
        recommended_action = "approve"

    return {
        "challenges": challenges,
        "risk_level": risk_level,
        "recommended_action": recommended_action,
    }


async def _llm_review(
    state: BriefingGraphState,
    llm: LLMRouter,
    *,
    trace_id: str,
) -> tuple[dict[str, object], LLMResponse | None]:
    settings = get_settings()
    messages = build_llm_messages(
        "adversarial",
        _build_adversarial_user_content(state),
        model=resolve_model_name(llm),
        enable_caching=settings.enable_prompt_caching,
    )
    try:
        response = await llm.generate(
            messages=messages,
            trace_id=trace_id,
            input_budget=ADVERSARIAL_INPUT_BUDGET,
            output_budget=ADVERSARIAL_OUTPUT_BUDGET,
            agent_id="adversarial",
            data_classification="confidential",
        )
        review = parse_llm_json(response.content)
    except (LLMError, json.JSONDecodeError) as exc:
        logger.warning("adversarial_llm_fallback", trace_id=trace_id, error=str(exc))
        return _review_outputs(state), None

    for key in ("challenges", "risk_level", "recommended_action"):
        if key not in review:
            return _review_outputs(state), response

    return review, response


async def adversarial_agent_node(
    state: BriefingGraphState,
    llm: LLMRouter | None = None,
) -> dict[str, Any]:
    """Run adversarial red-team review via LLM with heuristic fallback."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    logger.info("adversarial_agent_started", trace_id=trace_id)

    llm_response: LLMResponse | None = None
    if llm is not None:
        review, llm_response = await _llm_review(state, llm, trace_id=trace_id)
    else:
        review = _review_outputs(state)

    execution_ms = int((time.perf_counter() - start) * 1000)
    envelope = _build_envelope(
        state=state,
        result=review,
        execution_ms=execution_ms,
        llm_response=llm_response,
    )

    update: dict[str, Any] = {
        "adversarial_result": envelope,
        "current_agent": "adversarial",
    }
    if llm_response is not None:
        update["total_tokens"] = state.get("total_tokens", 0) + llm_response.tokens_used

    return update
