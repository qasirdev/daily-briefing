"""Briefing generation endpoints."""

from __future__ import annotations

import time
from datetime import UTC, date, datetime
from typing import cast
from uuid import uuid4

import structlog
from fastapi import APIRouter, HTTPException, Request, status

from backend.dependencies import build_llm_router, build_mcp_clients
from backend.graph.builder import build_briefing_graph
from backend.graph.state import BriefingGraphState
from backend.metrics import record_briefing_generation
from backend.schemas.briefing import (
    AgentExecutionSummary,
    BriefingMetadata,
    BriefingRequest,
    BriefingResponse,
)
from backend.schemas.consent import ConsentPromptRequest
from backend.schemas.envelope import AgentResultEnvelope
from backend.security.rate_limit import limiter
from backend.settings import get_settings
from backend.telemetry import start_async_span

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/briefing", tags=["briefing"])

_AGENT_KEYS = (
    ("task", "task_result"),
    ("calendar", "calendar_result"),
    ("focus", "focus_result"),
    ("critic", "critic_result"),
    ("orchestrator", "orchestrator_result"),
)


def _build_agent_breakdown(
    result: BriefingGraphState,
) -> tuple[list[str], list[AgentExecutionSummary], str]:
    agents_invoked: list[str] = []
    breakdown: list[AgentExecutionSummary] = []
    primary_model = "none"

    for name, key in _AGENT_KEYS:
        envelope = result.get(key)
        if not isinstance(envelope, AgentResultEnvelope):
            continue
        agents_invoked.append(name)
        if envelope.metadata.model_used != "none":
            primary_model = envelope.metadata.model_used
        breakdown.append(
            AgentExecutionSummary(
                agent_id=name,
                execution_ms=envelope.metadata.execution_ms,
                tokens_used=envelope.metadata.tokens_used,
                model_used=envelope.metadata.model_used,
                status=envelope.status,
            ),
        )

    return agents_invoked, breakdown, primary_model


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
        "consent_request": None,
        "dlq_events": [],
        "orchestrator_result": None,
        "task_result": None,
        "calendar_result": None,
        "focus_result": None,
        "critic_result": None,
    }

    try:
        async with start_async_span("generate_briefing", request_id=body.user_id):
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

    result_state = cast(BriefingGraphState, result)
    execution_ms = int((time.perf_counter() - started) * 1000)
    graph_status = result_state.get("status", "failure")

    if result_state.get("consent_required") or graph_status == "awaiting_consent":
        response_status = "awaiting_consent"
    elif graph_status == "degraded":
        response_status = "degraded"
    elif graph_status == "success":
        response_status = "success"
    else:
        response_status = "failure"

    agents_invoked, agent_breakdown, model_used = _build_agent_breakdown(result_state)

    record_briefing_generation(
        status=response_status,
        degraded=response_status == "degraded",
        duration_seconds=execution_ms / 1000,
    )

    logger.info(
        "briefing_generation_complete",
        trace_id=trace_id,
        status=response_status,
        execution_ms=execution_ms,
    )

    consent_request: ConsentPromptRequest | None = None
    raw_consent = result_state.get("consent_request")
    if isinstance(raw_consent, dict):
        consent_request = ConsentPromptRequest.model_validate(raw_consent)

    return BriefingResponse(
        status=response_status,  # type: ignore[arg-type]
        briefing=result_state.get("final_briefing") or "",
        metadata=BriefingMetadata(
            trace_id=trace_id,
            total_tokens=result_state.get("total_tokens", 0),
            execution_ms=execution_ms,
            model_used=model_used,
            agents_invoked=agents_invoked,
            agent_breakdown=agent_breakdown,
        ),
        consent_context=result_state.get("consent_context"),
        consent_request=consent_request,
    )
