"""Health and readiness HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from backend.health.checks import ReadinessResponse, run_readiness_checks
from backend.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(response: Response) -> ReadinessResponse:
    settings = get_settings()
    report = await run_readiness_checks(settings)
    if report.status == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return report
