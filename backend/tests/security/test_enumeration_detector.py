"""Tests for account enumeration detection (T1087)."""

from __future__ import annotations

from unittest.mock import patch

from backend.security.enumeration_detector import EnumerationDetector
from backend.settings import Settings


def test_probe_within_threshold_no_alert() -> None:
    detector = EnumerationDetector(
        Settings(enumeration_probe_threshold=5, enumeration_window_seconds=60),
    )
    with patch("backend.security.enumeration_detector.record_security_alert") as mock_alert:
        for _ in range(5):
            fired = detector.record_probe(probe_type="consent_list", subject="user-a")
        assert fired is False
        mock_alert.assert_not_called()


def test_probe_exceeds_threshold_fires_alert() -> None:
    detector = EnumerationDetector(
        Settings(enumeration_probe_threshold=3, enumeration_window_seconds=60),
    )
    with patch("backend.security.enumeration_detector.record_security_alert") as mock_alert:
        fired = False
        for _ in range(4):
            fired = detector.record_probe(probe_type="consent_list", subject="user-b")
        assert fired is True
        mock_alert.assert_called_once()


def test_admin_whitelisted() -> None:
    detector = EnumerationDetector(Settings(enumeration_probe_threshold=1))
    with patch("backend.security.enumeration_detector.record_security_alert") as mock_alert:
        for _ in range(10):
            fired = detector.record_probe(
                probe_type="consent_list",
                subject="user-c",
                is_admin=True,
            )
        assert fired is False
        mock_alert.assert_not_called()


def test_reset_clears_windows() -> None:
    detector = EnumerationDetector(Settings(enumeration_probe_threshold=1))
    detector.record_probe(probe_type="credential_issue", subject="user-d")
    detector.reset()
    with patch("backend.security.enumeration_detector.record_security_alert") as mock_alert:
        fired = detector.record_probe(probe_type="credential_issue", subject="user-d")
        assert fired is False
        mock_alert.assert_not_called()


def test_mitre_t1087_detected_status() -> None:
    from backend.security.mitre_coverage import get_technique

    technique = get_technique("T1087")
    assert technique is not None
    assert technique.status == "detected"
