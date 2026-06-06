"""MITRE ATT&CK coverage tests (Gap #129)."""

from __future__ import annotations

import pytest

from backend.security.mitre_coverage import (
    TECHNIQUE_REGISTRY,
    get_coverage_summary,
    get_technique,
    list_blind_spots,
)


def test_registry_has_at_least_twenty_techniques() -> None:
    assert len(TECHNIQUE_REGISTRY) >= 20


def test_no_duplicate_technique_ids() -> None:
    ids = [t.technique_id for t in TECHNIQUE_REGISTRY]
    assert len(ids) == len(set(ids))


def test_coverage_ratio_meets_target() -> None:
    summary = get_coverage_summary()
    assert summary["coverage_ratio"] >= 0.80
    assert summary["applicable"] >= 18


def test_get_technique_lookup() -> None:
    mapping = get_technique("T1078")
    assert mapping is not None
    assert mapping.name == "Valid Accounts"
    assert mapping.status == "detected"


def test_unknown_technique_returns_none() -> None:
    assert get_technique("T9999") is None


def test_blind_spots_list() -> None:
    blind = list_blind_spots()
    assert isinstance(blind, list)


@pytest.mark.parametrize(
    ("technique_id", "expected_status"),
    [
        ("T1566.001", "detected"),
        ("T1078", "detected"),
        ("T1059", "not_applicable"),
    ],
)
def test_key_techniques_mapped(technique_id: str, expected_status: str) -> None:
    mapping = get_technique(technique_id)
    assert mapping is not None
    assert mapping.status == expected_status


def test_each_detected_technique_has_metric_reference() -> None:
    detected = [t for t in TECHNIQUE_REGISTRY if t.status == "detected"]
    for technique in detected:
        assert technique.detection_control
        assert technique.metric_or_audit
