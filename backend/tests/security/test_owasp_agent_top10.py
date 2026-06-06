"""OWASP Agent Top 10 compliance tests (Gaps #62-65)."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.security.owasp_agent import (
    AGENT_CONTROLS,
    AgentControl,
    compliance_summary,
    get_control,
)


@pytest.mark.parametrize("control", AGENT_CONTROLS, ids=lambda c: c.agent_id)
def test_each_agent_id_registered(control: AgentControl) -> None:
    assert control.agent_id.startswith("AGENT")
    assert control.name
    assert control.control


@pytest.mark.parametrize("control", AGENT_CONTROLS, ids=lambda c: c.agent_id)
def test_implemented_controls_have_tests(control: AgentControl) -> None:
    if control.status == "not_applicable":
        pytest.skip("N/A control")
    assert control.test_module, f"{control.agent_id} missing test_module"
    repo_root = Path(__file__).resolve().parents[3]
    test_path = repo_root / control.test_module
    assert test_path.is_file(), f"{control.agent_id} test missing: {control.test_module}"


def test_all_ten_agent_ids_present() -> None:
    ids = {c.agent_id for c in AGENT_CONTROLS}
    expected = {f"AGENT0{i}" for i in range(1, 10)} | {"AGENT10"}
    assert ids == expected


def test_compliance_summary_counts() -> None:
    summary = compliance_summary()
    assert sum(summary.values()) == 10
    assert summary["implemented"] + summary["partial"] + summary["not_applicable"] == 10


def test_agent01_goal_hijack_control() -> None:
    control = get_control("AGENT01")
    assert control is not None
    assert control.status == "implemented"
    assert "Constitutional" in control.control or "Injection" in control.control


def test_agent10_rogue_agents_control() -> None:
    control = get_control("AGENT10")
    assert control is not None
    assert control.status == "implemented"
    assert "drift" in control.control.lower()


def test_agent09_consent_payload_control() -> None:
    control = get_control("AGENT09")
    assert control is not None
    assert control.status in ("implemented", "partial")
    assert "action_payload" in control.control.lower() or "payload" in control.control.lower()
