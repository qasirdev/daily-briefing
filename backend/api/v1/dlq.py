"""Dead letter queue admin endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from backend.dlq.store import dlq_store
from backend.schemas.dlq import DLQEventSummary, DLQRetryResponse

router = APIRouter(prefix="/api/v1/dlq", tags=["dlq"])


def require_admin(
    request: Request,
    x_admin_key: str | None = Header(default=None),
) -> None:
    settings = getattr(request.app.state, "settings", None)
    if settings is None:
        from backend.settings import get_settings

        settings = get_settings()
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API is not configured",
        )
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")


@router.get("", response_model=list[DLQEventSummary])
async def list_dlq_events(_: None = Depends(require_admin)) -> list[DLQEventSummary]:
    """List failed agent events (admin only)."""
    return [
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
        )
        for event in dlq_store.list_events()
    ]


@router.post("/{event_id}/retry", response_model=DLQRetryResponse)
async def retry_dlq_event(
    event_id: UUID,
    _: None = Depends(require_admin),
) -> DLQRetryResponse:
    """Retry a failed briefing attempt from the DLQ (admin only)."""
    event = dlq_store.get(event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="DLQ event not found")

    allowed, message = dlq_store.can_retry(event)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

    dlq_store.mark_retry(event_id)
    return DLQRetryResponse(
        event_id=event_id,
        status="retry_started",
        message=f"Retry accepted for user {event.user_id}; invoke briefing generate separately",
    )
