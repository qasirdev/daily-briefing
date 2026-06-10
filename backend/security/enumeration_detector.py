"""Account enumeration detection (MITRE T1087)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock

import structlog

from backend.metrics import record_enumeration_attempt, record_mitre_detection
from backend.observability.drift_monitor import record_security_alert
from backend.settings import Settings, get_settings

logger = structlog.get_logger()


@dataclass
class _ProbeWindow:
    timestamps: deque[float] = field(default_factory=deque)
    lock: Lock = field(default_factory=Lock)


class EnumerationDetector:
    """Detect rapid identity/consent probes indicative of account enumeration."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._windows: dict[str, _ProbeWindow] = defaultdict(_ProbeWindow)

    def record_probe(
        self,
        *,
        probe_type: str,
        subject: str,
        is_admin: bool = False,
    ) -> bool:
        """Record a probe; return True if threshold exceeded (alert fired)."""
        if is_admin:
            record_enumeration_attempt(probe_type=probe_type, outcome="admin_whitelisted")
            return False

        window = self._windows[subject]
        now = time.monotonic()
        cutoff = now - self._settings.enumeration_window_seconds
        threshold = self._settings.enumeration_probe_threshold

        with window.lock:
            while window.timestamps and window.timestamps[0] < cutoff:
                window.timestamps.popleft()
            window.timestamps.append(now)
            count = len(window.timestamps)

        if count <= threshold:
            record_enumeration_attempt(probe_type=probe_type, outcome="within_threshold")
            return False

        record_enumeration_attempt(probe_type=probe_type, outcome="threshold_exceeded")
        record_mitre_detection(technique_id="T1087", coverage="detected")
        record_security_alert(alert_type="enumeration", severity="high")
        logger.warning(
            "enumeration_threshold_exceeded",
            probe_type=probe_type,
            subject=subject,
            count=count,
            window_seconds=self._settings.enumeration_window_seconds,
        )
        return True

    def reset(self) -> None:
        """Clear probe windows (for tests)."""
        self._windows.clear()


enumeration_detector = EnumerationDetector()
