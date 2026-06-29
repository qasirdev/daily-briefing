"""Real-time drift detection and dwell-time tracking (Gap #99)."""

from __future__ import annotations

from backend.observability.drift_monitor import (
    get_alert_investigation_coverage,
    get_dwell_time_samples,
    record_agent_violation,
    record_security_alert,
    record_security_incident,
)


def dwell_time_p95_seconds() -> float:
    """Return P95 dwell time in seconds; 0 when no samples exist."""
    samples = sorted(get_dwell_time_samples())
    if not samples:
        return 0.0
    index = max(0, int(len(samples) * 0.95) - 1)
    return samples[index]


class SecurityMonitor:
    """Facade over observability drift and dwell-time metrics."""

    record_violation = staticmethod(record_agent_violation)
    record_incident = staticmethod(record_security_incident)
    record_alert = staticmethod(record_security_alert)
    dwell_time_p95 = staticmethod(dwell_time_p95_seconds)
    alert_coverage = staticmethod(get_alert_investigation_coverage)
