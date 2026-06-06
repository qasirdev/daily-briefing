"""Cryptographically sealed security audit log (Gaps #123, #51)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

from backend.observability.metrics import (
    record_audit_chain_verification_failure,
    record_audit_log_entry,
)

logger = structlog.get_logger()

GENESIS_HASH = "0" * 64

AuditEventType = Literal[
    "credential_issued",
    "credential_revoked",
    "consent_granted",
    "guardrail_violation",
    "delegation_created",
]


class AuditEntry(BaseModel):
    """Single tamper-evident audit log entry in a hash chain."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: AuditEventType
    actor_id: str
    resource: str
    payload_hash: str
    prev_hash: str
    entry_hash: str


def _canonical_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def hash_payload(payload: dict[str, Any]) -> str:
    """Hash payload content — raw PII is never stored, only payload_hash."""
    return hashlib.sha256(_canonical_payload(payload).encode()).hexdigest()


def compute_entry_hash(*, prev_hash: str, entry_body: dict[str, Any]) -> str:
    """Compute SHA-256 chain link: sha256(prev_hash + canonical_json)."""
    canonical = json.dumps(entry_body, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(f"{prev_hash}{canonical}".encode()).hexdigest()
    return digest


def verify_audit_chain(entries: list[AuditEntry]) -> bool:
    """Return True when the full hash chain is intact; empty chain is valid."""
    if not entries:
        return True

    prev_hash = GENESIS_HASH
    for entry in entries:
        if entry.prev_hash != prev_hash:
            record_audit_chain_verification_failure()
            return False
        body = {
            "id": entry.id,
            "timestamp": entry.timestamp.isoformat(),
            "event_type": entry.event_type,
            "actor_id": entry.actor_id,
            "resource": entry.resource,
            "payload_hash": entry.payload_hash,
            "prev_hash": entry.prev_hash,
        }
        expected = compute_entry_hash(prev_hash=prev_hash, entry_body=body)
        if entry.entry_hash != expected:
            record_audit_chain_verification_failure()
            return False
        prev_hash = entry.entry_hash
    return True


class AuditLogWriter:
    """Append-only in-memory audit log with hash-chain sealing."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []
        self._lock_tail = GENESIS_HASH

    @property
    def entries(self) -> list[AuditEntry]:
        return list(self._entries)

    def append(
        self,
        *,
        event_type: AuditEventType,
        actor_id: str,
        resource: str,
        payload: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """Append a sealed audit entry and extend the hash chain."""
        payload_hash = hash_payload(payload or {})
        entry_id = str(uuid4())
        timestamp = datetime.now(UTC)
        prev_hash = self._lock_tail if self._entries else GENESIS_HASH
        body = {
            "id": entry_id,
            "timestamp": timestamp.isoformat(),
            "event_type": event_type,
            "actor_id": actor_id,
            "resource": resource,
            "payload_hash": payload_hash,
            "prev_hash": prev_hash,
        }
        entry_hash = compute_entry_hash(prev_hash=prev_hash, entry_body=body)
        entry = AuditEntry(
            id=entry_id,
            timestamp=timestamp,
            event_type=event_type,
            actor_id=actor_id,
            resource=resource,
            payload_hash=payload_hash,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )
        self._entries.append(entry)
        self._lock_tail = entry_hash
        record_audit_log_entry(event_type=event_type)
        logger.info(
            "audit_log_appended",
            event_type=event_type,
            actor_id=actor_id,
            resource=resource,
            entry_hash=entry_hash,
        )
        return entry

    def verify(self) -> bool:
        """Verify the integrity of all stored entries."""
        return verify_audit_chain(self._entries)


audit_log_writer = AuditLogWriter()
