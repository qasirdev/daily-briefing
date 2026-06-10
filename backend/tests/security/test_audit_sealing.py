"""Tests for cryptographically sealed audit log (DB-123)."""

from datetime import UTC, datetime

import pytest

from backend.observability.metrics import AUDIT_LOG_ENTRIES_TOTAL
from backend.security.audit import (
    GENESIS_HASH,
    AuditLogWriter,
    compute_entry_hash,
    hash_payload,
    verify_audit_chain,
)


@pytest.fixture
def writer() -> AuditLogWriter:
    return AuditLogWriter()


def test_empty_chain_verifies_true() -> None:
    assert verify_audit_chain([]) is True


def test_append_three_entries_verifies_chain(writer: AuditLogWriter) -> None:
    for index in range(3):
        writer.append(
            event_type="delegation_created",
            actor_id=f"agent-{index}",
            resource="google_calendar",
            payload={"step": index},
        )
    assert writer.verify() is True
    assert len(writer.entries) == 3
    assert writer.entries[0].prev_hash == GENESIS_HASH


def test_tampered_entry_hash_fails_verification(writer: AuditLogWriter) -> None:
    writer.append(
        event_type="consent_granted",
        actor_id="user-1",
        resource="google_calendar",
        payload={"consent_id": "abc"},
    )
    writer.append(
        event_type="credential_issued",
        actor_id="user-1",
        resource="google_calendar",
        payload={"intent": "read_events"},
    )
    entries = writer.entries
    tampered = entries[1].model_copy(update={"entry_hash": "f" * 64})
    assert verify_audit_chain([entries[0], tampered]) is False


def test_tampered_prev_hash_fails_verification(writer: AuditLogWriter) -> None:
    writer.append(
        event_type="consent_granted",
        actor_id="user-1",
        resource="google_calendar",
    )
    writer.append(
        event_type="credential_issued",
        actor_id="user-1",
        resource="google_calendar",
    )
    entries = writer.entries
    tampered = entries[1].model_copy(update={"prev_hash": "a" * 64})
    assert verify_audit_chain([entries[0], tampered]) is False


def test_payload_hash_excludes_raw_pii(writer: AuditLogWriter) -> None:
    entry = writer.append(
        event_type="credential_issued",
        actor_id="user-1",
        resource="google_calendar",
        payload={"email": "user@example.com", "token": "secret"},
    )
    assert entry.payload_hash == hash_payload({"email": "user@example.com", "token": "secret"})
    assert "user@example.com" not in entry.model_dump_json()


def test_compute_entry_hash_is_deterministic() -> None:
    body = {
        "id": "1",
        "timestamp": datetime(2026, 6, 6, tzinfo=UTC).isoformat(),
        "event_type": "consent_granted",
        "actor_id": "user-1",
        "resource": "google_calendar",
        "payload_hash": "abc",
        "prev_hash": GENESIS_HASH,
    }
    first = compute_entry_hash(prev_hash=GENESIS_HASH, entry_body=body)
    second = compute_entry_hash(prev_hash=GENESIS_HASH, entry_body=body)
    assert first == second


def test_audit_log_entries_metric_increments(writer: AuditLogWriter) -> None:
    before = AUDIT_LOG_ENTRIES_TOTAL.labels(event_type="guardrail_violation")._value.get()
    writer.append(
        event_type="guardrail_violation",
        actor_id="critic",
        resource="briefing",
        payload={"violation": "injection"},
    )
    after = AUDIT_LOG_ENTRIES_TOTAL.labels(event_type="guardrail_violation")._value.get()
    assert after == before + 1


def test_first_entry_uses_genesis_prev_hash(writer: AuditLogWriter) -> None:
    entry = writer.append(
        event_type="delegation_created",
        actor_id="orchestrator",
        resource="task_agent",
    )
    assert entry.prev_hash == GENESIS_HASH
