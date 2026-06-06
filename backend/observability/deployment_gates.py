"""Deployment gates on observability metrics (Gap #59)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from backend.security.mitre_coverage import get_coverage_summary
from backend.settings import Settings, get_settings

GateStatus = Literal["pass", "fail", "warn"]


@dataclass(frozen=True, slots=True)
class DeploymentGate:
    """Single deployment readiness gate."""

    gate_id: str
    name: str
    status: GateStatus
    target: str
    actual: str
    message: str = ""


@dataclass(frozen=True, slots=True)
class DeploymentGateReport:
    """Aggregate deployment gate evaluation."""

    gates: tuple[DeploymentGate, ...]
    all_pass: bool
    warn_only: bool


def check_deployment_gates(settings: Settings | None = None) -> DeploymentGateReport:
    """Evaluate metric-based deployment gates."""
    resolved = settings or get_settings()
    warn_only = resolved.app_env == "development"

    mitre = get_coverage_summary()
    coverage_ratio = float(mitre.get("coverage_ratio", 0.0))

    from backend.observability.drift_monitor import get_alert_investigation_coverage

    alert_coverage = get_alert_investigation_coverage()

    gates: list[DeploymentGate] = []

    mitre_status: GateStatus = "pass" if coverage_ratio >= 0.80 else "fail"
    if warn_only and mitre_status == "fail":
        mitre_status = "warn"
    gates.append(
        DeploymentGate(
            gate_id="mitre_coverage",
            name="MITRE ATT&CK Coverage",
            status=mitre_status,
            target="≥0.80",
            actual=f"{coverage_ratio:.2f}",
        ),
    )

    alert_status: GateStatus = "pass" if alert_coverage >= 0.95 else "fail"
    if warn_only and alert_status == "fail":
        alert_status = "warn"
    gates.append(
        DeploymentGate(
            gate_id="alert_investigation",
            name="Alert Investigation Coverage",
            status=alert_status,
            target="≥0.95",
            actual=f"{alert_coverage:.2f}",
        ),
    )

    gates.append(
        DeploymentGate(
            gate_id="agentic_rag",
            name="Agentic RAG Enabled",
            status="pass" if resolved.enable_agentic_rag else "warn",
            target="true",
            actual=str(resolved.enable_agentic_rag).lower(),
        ),
    )

    gates.append(
        DeploymentGate(
            gate_id="context_compression",
            name="Context Compression Budget",
            status="pass" if resolved.context_compression_max_chars >= 4000 else "fail",
            target="≥4000 chars",
            actual=str(resolved.context_compression_max_chars),
        ),
    )

    gate_tuple = tuple(gates)
    all_pass = all(g.status == "pass" for g in gate_tuple)
    return DeploymentGateReport(gates=gate_tuple, all_pass=all_pass, warn_only=warn_only)
