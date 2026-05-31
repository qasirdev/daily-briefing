"""Health and readiness check helpers."""

from __future__ import annotations

import asyncio
import time
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field

from backend.settings import Settings

CHECK_TIMEOUT_SECONDS = 5.0


class HealthCheckResult(BaseModel):
    """Result of a single dependency probe."""

    model_config = ConfigDict(strict=True)

    name: str
    status: Literal["healthy", "unhealthy", "degraded"]
    latency_ms: int = Field(..., ge=0)
    detail: str = ""


class ReadinessResponse(BaseModel):
    """Aggregated readiness probe response."""

    model_config = ConfigDict(strict=True)

    status: Literal["healthy", "degraded", "unhealthy"]
    checks: list[HealthCheckResult]


async def _probe_tcp(name: str, host: str, port: int) -> HealthCheckResult:
    start = time.perf_counter()
    try:
        _reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=CHECK_TIMEOUT_SECONDS,
        )
        writer.close()
        await writer.wait_closed()
        latency_ms = int((time.perf_counter() - start) * 1000)
        return HealthCheckResult(name=name, status="healthy", latency_ms=latency_ms)
    except TimeoutError:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return HealthCheckResult(
            name=name,
            status="unhealthy",
            latency_ms=latency_ms,
            detail="timeout",
        )
    except OSError as exc:
        latency_ms = int((time.perf_counter() - start) * 1000)
        return HealthCheckResult(
            name=name,
            status="unhealthy",
            latency_ms=latency_ms,
            detail=str(exc),
        )


def _check_llm_config(settings: Settings) -> HealthCheckResult:
    start = time.perf_counter()
    if settings.local_llm_enabled or settings.openrouter_api_key:
        latency_ms = int((time.perf_counter() - start) * 1000)
        provider = "local" if settings.local_llm_enabled else "openrouter"
        return HealthCheckResult(
            name="llm_provider",
            status="healthy",
            latency_ms=latency_ms,
            detail=provider,
        )
    latency_ms = int((time.perf_counter() - start) * 1000)
    return HealthCheckResult(
        name="llm_provider",
        status="unhealthy",
        latency_ms=latency_ms,
        detail="no LLM provider configured",
    )


async def run_readiness_checks(settings: Settings) -> ReadinessResponse:
    """Run all readiness probes concurrently."""
    parsed_db = urlparse(settings.database_url)
    db_host = parsed_db.hostname or "localhost"
    db_port = parsed_db.port or 5432

    checks = await asyncio.gather(
        _probe_tcp("postgres_mcp", settings.postgres_mcp_host, settings.postgres_mcp_port),
        _probe_tcp("calendar_mcp", settings.calendar_mcp_host, settings.calendar_mcp_port),
        _probe_tcp("database", db_host, db_port),
        _probe_tcp(
            "otel_collector",
            urlparse(settings.otel_exporter_otlp_endpoint).hostname or "localhost",
            urlparse(settings.otel_exporter_otlp_endpoint).port or 4317,
        ),
        asyncio.to_thread(_check_llm_config, settings),
    )

    statuses = [check.status for check in checks]
    if any(status == "unhealthy" for status in statuses):
        aggregate: Literal["healthy", "degraded", "unhealthy"] = "unhealthy"
    elif any(status == "degraded" for status in statuses):
        aggregate = "degraded"
    else:
        aggregate = "healthy"

    return ReadinessResponse(status=aggregate, checks=list(checks))
