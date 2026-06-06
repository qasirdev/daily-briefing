"""Verification agent LangGraph node (stub — full LLM implementation in Week 2)."""

from __future__ import annotations

import json
import time
from typing import Any, Literal

import structlog

from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata

logger = structlog.get_logger()

PROMPT_VERSION = "v1.0.0"


def _build_envelope(
    *,
    state: BriefingGraphState,
    status: Literal["success", "failure", "escalated"],
    result: dict[str, object],
    execution_ms: int,
    escalation: EscalationPayload | None = None,
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
            tokens_used=0,
            model_used="none",
            prompt_version=PROMPT_VERSION,
            trace_id=trace_id,
            data_classification="internal",
        ),
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


async def verification_agent_node(state: BriefingGraphState) -> dict[str, Any]:
    """Run heuristic verification of focus output against MCP source data."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    logger.info("verification_agent_started", trace_id=trace_id)

    verification = _verify_focus_against_sources(state)
    execution_ms = int((time.perf_counter() - start) * 1000)

    if verification["status"] == "discrepancies_found":
        flagged_raw = verification.get("flagged_claims", [])
        flagged_list = flagged_raw if isinstance(flagged_raw, list) else []
        critical_count = sum(
            1
            for item in flagged_list
            if isinstance(item, dict) and item.get("severity") in {"critical", "major"}
        )
        envelope = _build_envelope(
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
        )
    else:
        envelope = _build_envelope(
            state=state,
            status="success",
            result=verification,
            execution_ms=execution_ms,
        )

    return {
        "verification_result": envelope,
        "current_agent": "verification",
    }
