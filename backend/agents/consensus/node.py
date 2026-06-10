"""Consensus evaluator node for multi-agent agreement assessment."""

from __future__ import annotations

from typing import Any, TypedDict

from backend.graph.state import BriefingGraphState
from backend.metrics import record_consensus_disagreement
from backend.schemas.envelope import AgentResultEnvelope


class ConsensusResult(TypedDict):
    """Consensus evaluation result used by route_consensus."""

    status: str
    major_concerns: int
    moderate_concerns: int
    minor_concerns: int
    agreement_level: str


def _count_verification_concerns(
    verification_result: AgentResultEnvelope | None,
) -> tuple[int, int, int]:
    """Count major, moderate, and minor concerns from verification output."""
    major = 0
    moderate = 0
    minor = 0

    if verification_result is None or verification_result.result is None:
        return major, moderate, minor

    if verification_result.status != "escalated":
        return major, moderate, minor

    flagged = verification_result.result.get("flagged_claims", [])
    if not isinstance(flagged, list):
        return major, moderate, minor

    for item in flagged:
        if not isinstance(item, dict):
            continue
        severity = item.get("severity")
        if severity == "critical":
            major += 1
        elif severity == "major":
            moderate += 1
        else:
            minor += 1

    return major, moderate, minor


def _count_adversarial_concerns(
    adversarial_result: AgentResultEnvelope | None,
) -> tuple[int, int, int]:
    """Count major, moderate, and minor concerns from adversarial output."""
    major = 0
    moderate = 0
    minor = 0

    if adversarial_result is None or adversarial_result.result is None:
        return major, moderate, minor

    challenges = adversarial_result.result.get("challenges", [])
    if not isinstance(challenges, list):
        return major, moderate, minor

    for item in challenges:
        if not isinstance(item, dict):
            continue
        severity = item.get("severity")
        if severity == "severe":
            major += 1
        elif severity == "moderate":
            moderate += 1
        else:
            minor += 1

    return major, moderate, minor


async def consensus_evaluator_node(state: BriefingGraphState) -> dict[str, Any]:
    """Aggregate Verification and Adversarial outputs for routing decisions."""
    verification_result = state.get("verification_result")
    adversarial_result = state.get("adversarial_result")

    v_major, v_moderate, v_minor = _count_verification_concerns(
        verification_result if isinstance(verification_result, AgentResultEnvelope) else None,
    )
    a_major, a_moderate, a_minor = _count_adversarial_concerns(
        adversarial_result if isinstance(adversarial_result, AgentResultEnvelope) else None,
    )

    major_concerns = v_major + a_major
    moderate_concerns = v_moderate + a_moderate
    minor_concerns = v_minor + a_minor

    if major_concerns == 0 and moderate_concerns == 0:
        agreement_level = "agreement"
    elif major_concerns == 0:
        agreement_level = "minor_disagreement"
    else:
        agreement_level = "major_disagreement"

    if agreement_level != "agreement":
        record_consensus_disagreement(agreement_level=agreement_level)

    consensus_result: ConsensusResult = {
        "status": "evaluated",
        "major_concerns": major_concerns,
        "moderate_concerns": moderate_concerns,
        "minor_concerns": minor_concerns,
        "agreement_level": agreement_level,
    }

    return {
        "consensus_result": consensus_result,
        "current_agent": "consensus_evaluator",
    }
