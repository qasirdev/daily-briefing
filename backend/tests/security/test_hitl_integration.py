"""Week 7 HITL + governance integration tests."""

from __future__ import annotations

from backend.consent.store import ConsentStore
from backend.schemas.consent import ConsentGrantRequest
from backend.security.hitl import all_layers_operational, layer_summary
from backend.security.owasp_agent import get_control
from backend.security.per_action_authz import ActionRequest, PerActionAuthorizer
from backend.security.policy_engine import PolicyEngine


def test_owasp_agent08_hitl_implemented() -> None:
    control = get_control("AGENT08")
    assert control is not None
    assert control.status == "implemented"
    assert "HITL" in control.control


def test_hitl_layers_operational() -> None:
    summary = layer_summary()
    assert summary["planned"] == 0
    assert all_layers_operational() is True


def test_per_action_authz_integrated_with_consent_store() -> None:
    store = ConsentStore()
    store.grant(
        ConsentGrantRequest(
            user_id="integration-user",
            service="google_calendar",
            scope=["calendar.readonly"],
            agent_id="calendar",
            ttl_hours=1,
        ),
    )
    authorizer = PerActionAuthorizer(PolicyEngine(consent=store))
    decision = authorizer.authorize(
        ActionRequest(
            user_id="integration-user",
            agent_id="calendar",
            service="google_calendar",
            action="mcp_tool",
            scope=["calendar.readonly"],
        ),
    )
    assert decision.allowed is True


def test_governance_hitl_mode_default_human_on_the_loop() -> None:
    from backend.observability.reasoning_trace import collect_reasoning_traces

    trace = collect_reasoning_traces({"trace_id": "e" * 32, "status": "success"})
    assert trace.hitl_mode == "human_on_the_loop"


def test_emergency_change_tiers_documented() -> None:
    from pathlib import Path

    governance = Path(__file__).resolve().parents[3] / "docs" / "GOVERNANCE.md"
    assert governance.is_file()
    text = governance.read_text(encoding="utf-8")
    assert "Tier 1" in text
    assert "Tier 2" in text
    assert "Tier 3" in text


def test_tabletop_five_incident_scenarios_documented() -> None:
    from pathlib import Path

    tabletop = Path(__file__).resolve().parents[3] / "docs" / "security" / "TABLETOP-EXERCISES.md"
    assert tabletop.is_file()
    text = tabletop.read_text(encoding="utf-8")
    assert "Incident 1" in text
    assert "Incident 5" in text
    assert "simultaneous" in text.lower() or "concurrent" in text.lower()
