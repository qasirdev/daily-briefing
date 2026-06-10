"""Dwell time SLO and alert investigation coverage tests (Gaps #134, #135)."""

from __future__ import annotations

import time
from collections.abc import Iterator

import pytest

from backend.observability.drift_monitor import (
    get_alert_investigation_coverage,
    get_dwell_time_samples,
    get_long_term_drift_ratio,
    is_long_term_drift_alert,
    record_agent_violation,
    record_alert_investigation,
    record_security_alert,
    record_security_incident,
    reset_drift_monitor_state,
)


@pytest.fixture(autouse=True)
def _reset_state() -> Iterator[None]:
    reset_drift_monitor_state()
    yield
    reset_drift_monitor_state()


def test_dwell_time_recorded_on_incident_to_alert() -> None:
    record_security_incident(incident_id="inc-1")
    time.sleep(0.01)
    dwell = record_security_alert(
        alert_type="injection",
        severity="critical",
        incident_id="inc-1",
    )
    assert dwell is not None
    assert dwell >= 0.0
    samples = get_dwell_time_samples()
    assert len(samples) == 1


def test_alert_without_incident_has_no_dwell_time() -> None:
    dwell = record_security_alert(alert_type="drift", severity="warning")
    assert dwell is None


def test_alert_investigation_coverage_defaults_to_one() -> None:
    assert get_alert_investigation_coverage() == 1.0


def test_alert_investigation_coverage_calculation() -> None:
    record_security_alert(alert_type="injection", severity="high")
    record_security_alert(alert_type="injection", severity="high")
    record_alert_investigation(alert_type="injection", severity="high")
    coverage = get_alert_investigation_coverage()
    assert coverage == 0.5


def test_long_term_drift_ratio_stable_baseline() -> None:
    for _ in range(14):
        record_agent_violation(agent_id="critic", window="7d")
    for _ in range(30):
        record_agent_violation(agent_id="critic", window="30d")
    ratio = get_long_term_drift_ratio(agent_id="critic")
    assert ratio == pytest.approx(2.0, rel=0.01)


def test_long_term_drift_alert_threshold() -> None:
    for _ in range(14):
        record_agent_violation(agent_id="focus", window="7d")
    for _ in range(2):
        record_agent_violation(agent_id="focus", window="30d")
    assert is_long_term_drift_alert(agent_id="focus", threshold=2.0) is True


def test_zero_violations_no_drift_alert() -> None:
    assert is_long_term_drift_alert(agent_id="task") is False


def test_full_investigation_coverage() -> None:
    record_security_alert(alert_type="drift", severity="critical")
    record_alert_investigation(alert_type="drift", severity="critical")
    assert get_alert_investigation_coverage() == 1.0
