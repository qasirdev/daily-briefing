"""Centralized rate limiting configuration."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import JSONResponse

from backend.logging_config import get_security_logger

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return 429 with Retry-After and log the violation."""
    retry_after = exc.detail.split("Retry after ")[-1] if exc.detail else "60"
    client_host = get_remote_address(request)
    get_security_logger().warning(
        "rate_limit_exceeded",
        endpoint=request.url.path,
        client_host=client_host,
        detail=str(exc.detail),
    )
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={"Retry-After": retry_after},
    )


def register_rate_limiting(app: Any) -> None:
    """Attach shared limiter and exception handler to the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
