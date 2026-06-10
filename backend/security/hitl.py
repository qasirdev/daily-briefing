"""Human-in-the-loop (HITL) layer registry (Gaps #66, #95)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

LayerStatus = Literal["implemented", "partial", "planned"]


@dataclass(frozen=True, slots=True)
class HitlLayer:
    """Maps an IBM HITL architecture layer to an implementation."""

    layer_id: str
    name: str
    owner: Literal["human", "agent", "shared"]
    status: LayerStatus
    control: str
    test_module: str | None = None
    notes: str = ""


HITL_LAYERS: tuple[HitlLayer, ...] = (
    HitlLayer(
        layer_id="input",
        name="Input",
        owner="human",
        status="implemented",
        control="BriefingRequest user_id + target_date; consent scope selection",
        test_module="backend/tests/test_consent.py",
    ),
    HitlLayer(
        layer_id="planning",
        name="Planning",
        owner="agent",
        status="implemented",
        control="Focus Agent generates work plan within token budget",
        test_module="backend/tests/agents/test_focus_memory.py",
    ),
    HitlLayer(
        layer_id="review",
        name="Review",
        owner="shared",
        status="implemented",
        control="Verification + Adversarial + Critic quality/safety gates",
        test_module="backend/tests/architecture/test_consensus.py",
    ),
    HitlLayer(
        layer_id="revision",
        name="Revision",
        owner="agent",
        status="implemented",
        control="Critic revision loop with revision_count cap",
        test_module="backend/tests/integration/test_langgraph.py",
    ),
    HitlLayer(
        layer_id="execution",
        name="Execution",
        owner="agent",
        status="implemented",
        control="MCP tool calls within scoped consent + per-action authz",
        test_module="backend/tests/security/test_per_action_authz.py",
    ),
    HitlLayer(
        layer_id="monitoring",
        name="Monitoring",
        owner="shared",
        status="implemented",
        control="Reasoning traces, drift detection, Prometheus metrics",
        test_module="backend/tests/observability/test_reasoning_trace.py",
    ),
    HitlLayer(
        layer_id="override",
        name="Override",
        owner="human",
        status="implemented",
        control="Consent deny/revoke, human escalation on consensus disagreement",
        test_module="backend/tests/security/test_hitl_layers.py",
    ),
    HitlLayer(
        layer_id="feedback",
        name="Feedback",
        owner="human",
        status="implemented",
        control="Reasoning-level feedback API + episodic distillation",
        test_module="backend/tests/test_reasoning_feedback.py",
        notes="ReasoningFeedback component on briefing page",
    ),
)


def get_layer(layer_id: str) -> HitlLayer | None:
    """Return HITL layer metadata by ID."""
    for layer in HITL_LAYERS:
        if layer.layer_id == layer_id.lower():
            return layer
    return None


def layer_summary() -> dict[str, int]:
    """Count layers by status."""
    summary = {"implemented": 0, "partial": 0, "planned": 0}
    for layer in HITL_LAYERS:
        summary[layer.status] += 1
    return summary


def all_layers_operational() -> bool:
    """True when every layer is implemented or partial (none planned)."""
    return all(layer.status != "planned" for layer in HITL_LAYERS)
