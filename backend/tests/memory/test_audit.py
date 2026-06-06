"""Tests for memory audit trail."""

from __future__ import annotations

from backend.memory.audit import MemoryAuditTrail

TRACE_ID = "a" * 32


def test_log_read_appends_structured_entry() -> None:
    trail = MemoryAuditTrail()
    entry = trail.log_read(
        trace_id=TRACE_ID,
        user_id="user-1",
        agent_id="focus",
        memory_layer="semantic",
        operation="search",
        result_count=2,
        request_id="req-1",
        query_summary="Q2 report | Sprint Review",
    )

    assert len(trail.entries) == 1
    assert trail.entries[0] is entry
    assert entry.memory_layer == "semantic"
    assert entry.operation == "search"
    assert entry.result_count == 2
    assert entry.query_summary == "Q2 report | Sprint Review"


def test_clear_resets_entries() -> None:
    trail = MemoryAuditTrail()
    trail.log_read(
        trace_id=TRACE_ID,
        user_id="user-1",
        agent_id="focus",
        memory_layer="working",
        operation="snapshot",
        result_count=1,
    )
    trail.clear()
    assert trail.entries == ()
