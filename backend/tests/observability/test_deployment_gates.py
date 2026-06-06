"""Tests for deployment gates on metrics."""

from __future__ import annotations

from backend.observability.deployment_gates import check_deployment_gates
from backend.settings import Settings


def test_development_warn_only_on_failures() -> None:
    report = check_deployment_gates(Settings(app_env="development", enable_agentic_rag=True))
    assert report.warn_only is True
    assert len(report.gates) >= 4


def test_production_requires_pass_or_fail() -> None:
    report = check_deployment_gates(
        Settings(
            app_env="production",
            enable_agentic_rag=True,
            jwt_secret_key="f" * 64,
            admin_api_key="test-admin-key",
            app_debug=False,
            local_llm_enabled=True,
        ),
    )
    assert report.warn_only is False


def test_agentic_rag_gate_passes_when_enabled() -> None:
    report = check_deployment_gates(Settings(enable_agentic_rag=True))
    rag_gate = next(g for g in report.gates if g.gate_id == "agentic_rag")
    assert rag_gate.status == "pass"


def test_context_compression_gate_fails_on_low_budget() -> None:
    report = check_deployment_gates(Settings(context_compression_max_chars=1000))
    compression_gate = next(g for g in report.gates if g.gate_id == "context_compression")
    assert compression_gate.status == "fail"


def test_mitre_gate_present() -> None:
    report = check_deployment_gates()
    mitre_gate = next(g for g in report.gates if g.gate_id == "mitre_coverage")
    assert mitre_gate.status in {"pass", "fail", "warn"}
