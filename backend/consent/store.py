"""In-memory consent store with audit logging."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import structlog

from backend.metrics import record_consent_request
from backend.schemas.consent import (
    AuditAction,
    ConsentAuditLog,
    ConsentGrantRequest,
    ConsentRecord,
    calculate_expires_at,
)

logger = structlog.get_logger()


class ConsentStore:
    """Process-local consent records keyed by user and service."""

    def __init__(self) -> None:
        self._records: dict[UUID, ConsentRecord] = {}
        self._audit: list[ConsentAuditLog] = []

    def _log(
        self,
        *,
        user_id: str,
        action: AuditAction,
        consent_id: UUID | None = None,
        service: str = "",
        details: str = "",
    ) -> None:
        entry = ConsentAuditLog(
            user_id=user_id,
            consent_id=consent_id,
            action=action,
            service=service,
            details=details,
        )
        self._audit.append(entry)
        logger.info(
            "consent_audit",
            user_id=user_id,
            action=action,
            consent_id=str(consent_id) if consent_id else None,
            service=service,
        )

    def _find_by_user_service(self, user_id: str, service: str) -> ConsentRecord | None:
        for record in self._records.values():
            if record.user_id == user_id and record.service == service and record.is_active:
                return record
        return None

    def grant(self, request: ConsentGrantRequest) -> ConsentRecord:
        if request.consent_type is not None:
            consent_type = request.consent_type
        elif request.ttl_hours == 0:
            consent_type = "session"
        elif request.ttl_hours >= 168:
            consent_type = "recurring"
        else:
            consent_type = "time_bounded"
        expires_at = calculate_expires_at(
            service=request.service,
            consent_type=consent_type,
            ttl_hours=request.ttl_hours,
        )
        existing = self._find_by_user_service(request.user_id, request.service)
        if existing is not None:
            updated = existing.model_copy(
                update={
                    "scope": request.scope,
                    "agent_id": request.agent_id,
                    "consent_type": consent_type,
                    "granted_at": datetime.now(UTC),
                    "expires_at": expires_at,
                    "revoked_at": None,
                    "revocation_reason": None,
                },
            )
            self._records[updated.id] = updated
            self._log(
                user_id=request.user_id,
                action="consent_granted",
                consent_id=updated.id,
                service=request.service,
                details="updated existing consent",
            )
            record_consent_request(mcp_server=request.service, outcome="granted")
            return updated

        record = ConsentRecord(
            user_id=request.user_id,
            service=request.service,
            scope=request.scope,
            agent_id=request.agent_id,
            consent_type=consent_type,
            expires_at=expires_at,
        )
        self._records[record.id] = record
        self._log(
            user_id=request.user_id,
            action="consent_granted",
            consent_id=record.id,
            service=request.service,
        )
        record_consent_request(mcp_server=request.service, outcome="granted")
        return record

    def list_active(self, user_id: str) -> list[ConsentRecord]:
        active = [
            record
            for record in self._records.values()
            if record.user_id == user_id and record.is_active
        ]
        return sorted(active, key=lambda item: item.granted_at, reverse=True)

    def get(self, consent_id: UUID) -> ConsentRecord | None:
        return self._records.get(consent_id)

    def revoke(self, consent_id: UUID, *, reason: str = "user_revoked") -> ConsentRecord | None:
        record = self._records.get(consent_id)
        if record is None:
            return None
        updated = record.model_copy(
            update={
                "revoked_at": datetime.now(UTC),
                "revocation_reason": reason,
            },
        )
        self._records[consent_id] = updated
        self._log(
            user_id=record.user_id,
            action="consent_revoked",
            consent_id=consent_id,
            service=record.service,
            details=reason,
        )
        record_consent_request(mcp_server=record.service, outcome="revoked")
        return updated

    def has_valid_consent(self, user_id: str, service: str) -> bool:
        record = self._find_by_user_service(user_id, service)
        if record is None:
            return False
        if not record.is_active:
            self._log(
                user_id=user_id,
                action="consent_expired",
                consent_id=record.id,
                service=service,
            )
            return False
        return True

    def record_usage(self, user_id: str, service: str) -> None:
        record = self._find_by_user_service(user_id, service)
        if record is None:
            return
        updated = record.model_copy(
            update={
                "times_used": record.times_used + 1,
                "last_used_at": datetime.now(UTC),
            },
        )
        self._records[record.id] = updated
        self._log(
            user_id=user_id,
            action="consent_used",
            consent_id=record.id,
            service=service,
        )

    def list_audit(self, user_id: str | None = None) -> list[ConsentAuditLog]:
        if user_id is None:
            return list(self._audit)
        return [entry for entry in self._audit if entry.user_id == user_id]

    def all_records_for_user(self, user_id: str) -> list[ConsentRecord]:
        return [record for record in self._records.values() if record.user_id == user_id]


consent_store = ConsentStore()
