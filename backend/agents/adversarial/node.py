"""Adversarial agent LangGraph node (stub — full LLM implementation in Week 2)."""

from __future__ import annotations

import time
from typing import Any, Literal

import structlog

from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata

logger = structlog.get_logger()

PROMPT_VERSION = "v1.0.0"


def _build_envelope(
    *,
    state: BriefingGraphState,
    result: dict[str, object],
    execution_ms: int,
) -> AgentResultEnvelope:
    trace_id = state.get("trace_id", "0" * 32)
    return AgentResultEnvelope(
        agent_id="adversarial",
        canonical_role="adversarial",
        status="success",
        result=result,
        metadata=ExecutionMetadata(
            execution_ms=execution_ms,
            tokens_used=0,
            model_used="none",
            prompt_version=PROMPT_VERSION,
            trace_id=trace_id,
            data_classification="internal",
        ),
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


async def adversarial_agent_node(state: BriefingGraphState) -> dict[str, Any]:
    """Run heuristic adversarial review for consensus routing."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    logger.info("adversarial_agent_started", trace_id=trace_id)

    review = _review_outputs(state)
    execution_ms = int((time.perf_counter() - start) * 1000)
    envelope = _build_envelope(state=state, result=review, execution_ms=execution_ms)

    return {
        "adversarial_result": envelope,
        "current_agent": "adversarial",
    }
