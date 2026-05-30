"""Briefing generation endpoints."""

from __future__ import annotations

import time
from datetime import UTC, date, datetime
from uuid import uuid4

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.dependencies import build_llm_router, build_mcp_clients
from backend.graph.builder import build_briefing_graph
from backend.graph.state import BriefingGraphState
from backend.schemas.briefing import BriefingMetadata, BriefingRequest, BriefingResponse
from backend.settings import get_settings

logger = structlog.get_logger()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/v1/briefing", tags=["briefing"])


@router.post("/generate", response_model=BriefingResponse)
@limiter.limit("10/minute")
async def generate_briefing(request: Request, body: BriefingRequest) -> BriefingResponse:
    """Generate a daily briefing by invoking the LangGraph pipeline."""
    settings = get_settings()
    trace_id = getattr(request.state, "trace_id", uuid4().hex)
    started = time.perf_counter()
    mcp = build_mcp_clients(settings)
    llm = build_llm_router(settings)
    graph = build_briefing_graph(mcp, llm, settings)

    initial_state: BriefingGraphState = {
        "user_id": body.user_id,
        "request_id": uuid4().hex,
        "trace_id": trace_id,
        "requested_at": datetime.now(UTC),
        "target_date": body.target_date or date.today(),
        "current_agent": "",
        "revision_count": 0,
        "total_tokens": 0,
        "graph_started_at": time.perf_counter(),
        "status": "pending",
        "final_briefing": None,
        "consent_required": False,
        "consent_context": None,
        "dlq_events": [],
        "orchestrator_result": None,
        "task_result": None,
        "calendar_result": None,
        "focus_result": None,
        "critic_result": None,
    }

    try:
        result = await graph.ainvoke(initial_state)
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Briefing generation timed out",
        ) from exc
    except Exception as exc:
        execution_ms = int((time.perf_counter() - started) * 1000)
        logger.exception("briefing_generation_failed", trace_id=trace_id, error=str(exc))
        return BriefingResponse(
            status="failure",
            briefing="",
            metadata=BriefingMetadata(
                trace_id=trace_id,
                total_tokens=0,
                execution_ms=execution_ms,
                agents_invoked=[],
            ),
            consent_context=str(exc),
        )
    finally:
        await mcp.close()

    execution_ms = int((time.perf_counter() - started) * 1000)
    graph_status = result.get("status", "failure")

    if result.get("consent_required"):
        response_status = "awaiting_consent"
    elif graph_status == "degraded":
        response_status = "degraded"
    elif graph_status == "success":
        response_status = "success"
    else:
        response_status = "failure"

    agents_invoked = [
        name
        for name in ("task", "calendar", "focus", "critic", "orchestrator")
        if result.get(f"{name}_result") or name == "orchestrator"
    ]

    logger.info(
        "briefing_generation_complete",
        trace_id=trace_id,
        status=response_status,
        execution_ms=execution_ms,
    )

    return BriefingResponse(
        status=response_status,  # type: ignore[arg-type]
        briefing=result.get("final_briefing") or "",
        metadata=BriefingMetadata(
            trace_id=trace_id,
            total_tokens=result.get("total_tokens", 0),
            execution_ms=execution_ms,
            agents_invoked=agents_invoked,
        ),
        consent_context=result.get("consent_context"),
    )
