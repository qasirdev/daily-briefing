"""Orchestrator presentation helpers."""

from backend.agents.orchestrator.node import format_event_time_london


def test_format_event_time_london_strips_seconds_and_offset() -> None:
    assert format_event_time_london("2026-06-03T13:00:00+01:00") == "2026-06-03T13:00"


def test_format_event_time_london_converts_utc_to_bst() -> None:
    assert format_event_time_london("2026-06-03T12:00:00+00:00") == "2026-06-03T13:00"


def test_format_event_time_london_all_day_date() -> None:
    assert format_event_time_london("2026-06-03") == "2026-06-03"


def test_format_event_time_london_interview_example() -> None:
    assert format_event_time_london("2026-06-05T14:30:00+01:00") == "2026-06-05T14:30"
