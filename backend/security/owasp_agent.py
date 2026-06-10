"""OWASP Agent Top 10 control registry (Gaps #62-65)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ControlStatus = Literal["implemented", "partial", "not_applicable"]


@dataclass(frozen=True, slots=True)
class AgentControl:
    """Maps an OWASP Agent Top 10 ID to an implemented control."""

    agent_id: str
    name: str
    status: ControlStatus
    control: str
    test_module: str | None = None
    notes: str = ""


AGENT_CONTROLS: tuple[AgentControl, ...] = (
    AgentControl(
        agent_id="AGENT01",
        name="Agent Goal Hijack",
        status="implemented",
        control=(
            "PromptInjectionDetector + PromptGuard 2 + ConstitutionalClassifier + Critic escalation"
        ),
        test_module="backend/tests/unit/test_security.py",
    ),
    AgentControl(
        agent_id="AGENT02",
        name="Tool Misuse",
        status="implemented",
        control="MCP scope boundaries, read-only SQL, SSRF allowlists",
        test_module="backend/tests/security/test_mcp_security.py",
    ),
    AgentControl(
        agent_id="AGENT03",
        name="Agentic Logic Abuse",
        status="implemented",
        control="Consensus workflow, Critic quality gate, revision limits",
        test_module="backend/tests/architecture/test_consensus.py",
    ),
    AgentControl(
        agent_id="AGENT04",
        name="Memory Poisoning",
        status="implemented",
        control="Memory quarantine workflow, ingestion injection scan",
        test_module="backend/tests/memory/test_quarantine.py",
    ),
    AgentControl(
        agent_id="AGENT05",
        name="Cascading Failures",
        status="implemented",
        control="DLQ routing, circuit breakers, token budget limits",
        test_module="backend/tests/security/test_token_budget.py",
    ),
    AgentControl(
        agent_id="AGENT06",
        name="Unexpected Code Execution",
        status="not_applicable",
        control="No agent-generated code execution in MVP scope",
        test_module=None,
        notes="Agents do not emit or execute arbitrary code",
    ),
    AgentControl(
        agent_id="AGENT07",
        name="Identity & Privilege Abuse",
        status="implemented",
        control="JIT CredentialBroker, consent validation, NHI registry",
        test_module="backend/tests/security/test_vault.py",
    ),
    AgentControl(
        agent_id="AGENT08",
        name="Overwhelming Human in the Loop",
        status="implemented",
        control=(
            "8-layer HITL architecture: consent, consensus escalation, "
            "reasoning traces, per-action authz, override paths"
        ),
        test_module="backend/tests/security/test_hitl_layers.py",
    ),
    AgentControl(
        agent_id="AGENT09",
        name="Human-Agent Trust Exploitation",
        status="implemented",
        control="Consent modal shows structured action_payload alongside natural-language message",
        test_module="backend/tests/security/test_governance_integration.py",
    ),
    AgentControl(
        agent_id="AGENT10",
        name="Rogue Agents",
        status="implemented",
        control="Guardrail violation trends, long-term drift ratio, red team cadence",
        test_module="backend/tests/observability/test_drift_detection.py",
    ),
)


def get_control(agent_id: str) -> AgentControl | None:
    """Return control metadata for an OWASP Agent ID."""
    for control in AGENT_CONTROLS:
        if control.agent_id == agent_id.upper():
            return control
    return None


def list_implemented_controls() -> list[AgentControl]:
    """Return controls with implemented or partial status."""
    return [c for c in AGENT_CONTROLS if c.status in ("implemented", "partial")]


def compliance_summary() -> dict[str, int]:
    """Count controls by status."""
    summary = {"implemented": 0, "partial": 0, "not_applicable": 0}
    for control in AGENT_CONTROLS:
        summary[control.status] += 1
    return summary
