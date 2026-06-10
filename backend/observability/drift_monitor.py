"""Long-term drift, dwell time, and alert investigation tracking (Gaps #122, #134, #135)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock

import structlog

logger = structlog.get_logger()

_lock = Lock()
_incident_timestamps: dict[str, float] = {}
_agent_violation_windows: dict[str, dict[str, int]] = {}


@dataclass
class AlertTracker:
    """In-process alert and investigation counters for coverage metrics."""

    alerts_total: dict[tuple[str, str], int] = field(default_factory=dict)
    alerts_investigated: dict[tuple[str, str], int] = field(default_factory=dict)
    dwell_times_seconds: list[float] = field(default_factory=list)


_tracker = AlertTracker()


def record_agent_violation(*, agent_id: str, window: str = "7d") -> None:
    """Record a guardrail violation for long-term drift baseline comparison."""
    with _lock:
        windows = _agent_violation_windows.setdefault(agent_id, {"7d": 0, "30d": 0})
        windows[window] = windows.get(window, 0) + 1


def get_long_term_drift_ratio(*, agent_id: str) -> float:
    """Return 7d/30d violation rate ratio for an agent (1.0 = stable)."""
    with _lock:
        windows = _agent_violation_windows.get(agent_id, {})
        count_7d = windows.get("7d", 0)
        count_30d = windows.get("30d", 0)

    if count_30d == 0:
        return 1.0 if count_7d == 0 else float(count_7d)

    baseline_rate = count_30d / 30.0
    recent_rate = count_7d / 7.0
    if baseline_rate == 0:
        return recent_rate if recent_rate > 0 else 1.0
    return recent_rate / baseline_rate


def is_long_term_drift_alert(*, agent_id: str, threshold: float = 2.0) -> bool:
    """Return True when 7d violation rate exceeds threshold × 30d baseline."""
    return get_long_term_drift_ratio(agent_id=agent_id) >= threshold


def record_security_incident(*, incident_id: str) -> None:
    """Mark the occurrence time of a security incident for dwell time tracking."""
    with _lock:
        _incident_timestamps[incident_id] = time.time()


def record_security_alert(
    *,
    alert_type: str,
    severity: str,
    incident_id: str | None = None,
) -> float | None:
    """Record alert firing; return dwell time seconds if incident_id matches prior incident."""
    key = (alert_type, severity)
    dwell_seconds: float | None = None

    with _lock:
        _tracker.alerts_total[key] = _tracker.alerts_total.get(key, 0) + 1

        if incident_id and incident_id in _incident_timestamps:
            dwell_seconds = time.time() - _incident_timestamps[incident_id]
            _tracker.dwell_times_seconds.append(dwell_seconds)
            del _incident_timestamps[incident_id]

    logger.info(
        "security_alert_recorded",
        alert_type=alert_type,
        severity=severity,
        dwell_seconds=dwell_seconds,
    )
    return dwell_seconds


def record_alert_investigation(*, alert_type: str, severity: str) -> None:
    """Mark an alert as investigated for coverage tracking."""
    key = (alert_type, severity)
    with _lock:
        _tracker.alerts_investigated[key] = _tracker.alerts_investigated.get(key, 0) + 1


def get_alert_investigation_coverage() -> float:
    """Return fraction of alerts investigated (0.0–1.0). Defaults to 1.0 when no alerts."""
    with _lock:
        total = sum(_tracker.alerts_total.values())
        investigated = sum(_tracker.alerts_investigated.values())

    if total == 0:
        return 1.0
    return min(investigated / total, 1.0)


def get_dwell_time_samples() -> list[float]:
    """Return recorded dwell time samples in seconds."""
    with _lock:
        return list(_tracker.dwell_times_seconds)


def reset_drift_monitor_state() -> None:
    """Reset in-process state — for tests only."""
    global _tracker
    with _lock:
        _incident_timestamps.clear()
        _agent_violation_windows.clear()
        _tracker = AlertTracker()
