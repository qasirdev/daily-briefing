"""GDPR data export endpoints."""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Query, Request, Response

from backend.consent.store import consent_store
from backend.dlq.store import dlq_store
from backend.preferences.store import preference_store
from backend.schemas.dlq import DLQEventSummary
from backend.security.rate_limit import limiter

router = APIRouter(prefix="/api/v1/export", tags=["export"])


def _build_export_payload(user_id: str) -> dict[str, object]:
    consents = consent_store.all_records_for_user(user_id)
    preferences = preference_store.list_for_user(user_id)
    dlq_events = [
        event
        for event in dlq_store.list_events()
        if event.user_id == user_id
    ]
    return {
        "user_id": user_id,
        "exported_at": datetime.now(UTC).isoformat(),
        "consent_records": [record.model_dump(mode="json") for record in consents],
        "consent_audit_log": [
            entry.model_dump(mode="json")
            for entry in consent_store.list_audit(user_id)
        ],
        "preferences": [pref.model_dump(mode="json") for pref in preferences],
        "dlq_events": [
            DLQEventSummary(
                id=event.id,
                request_id=event.request_id,
                user_id=event.user_id,
                agent_id=event.agent_id,
                reason=event.reason,
                trace_id=event.trace_id,
                created_at=event.created_at,
                retried_at=event.retried_at,
                retry_count=event.retry_count,
            ).model_dump(mode="json")
            for event in dlq_events
        ],
        "briefing_history": [],
    }


def _to_csv(payload: dict[str, object]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["section", "json"])
    for key, value in payload.items():
        writer.writerow([key, json.dumps(value, ensure_ascii=True)])
    return buffer.getvalue()


@router.get("")
@limiter.limit("5/hour")
async def export_user_data(
    request: Request,
    user_id: str = Query(..., min_length=1),
    format: Literal["json", "csv"] = Query(default="json"),
) -> Response:
    """Export all stored user data for GDPR requests."""
    payload = _build_export_payload(user_id)
    if format == "csv":
        content = _to_csv(payload)
        media_type = "text/csv"
        filename = f"export-{user_id}.csv"
    else:
        content = json.dumps(payload, indent=2, ensure_ascii=True)
        media_type = "application/json"
        filename = f"export-{user_id}.json"

    if not any(
        [
            payload["consent_records"],
            payload["preferences"],
            payload["dlq_events"],
            payload["consent_audit_log"],
        ],
    ):
        payload["message"] = "No stored data for user"
        content = json.dumps(payload, indent=2, ensure_ascii=True)

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
