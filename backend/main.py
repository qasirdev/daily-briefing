"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.api.v1.briefing import limiter
from backend.api.v1.briefing import router as briefing_router
from backend.api.v1.consent import router as consent_router
from backend.api.v1.dlq import router as dlq_router
from backend.api.v1.export import router as export_router
from backend.api.v1.preferences import router as preferences_router
from backend.logging_config import bind_trace_id, configure_logging, get_logger
from backend.settings import Settings, get_settings
from backend.telemetry import configure_telemetry, trace_id_from_span

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — configure logging and telemetry on startup."""
    settings = get_settings()
    configure_logging(debug=settings.app_debug)
    configure_telemetry(settings)
    logger.info("application_started", app_env=settings.app_env, version=settings.app_version)
    yield
    logger.info("application_shutdown")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    resolved_settings = settings or get_settings()

    app = FastAPI(
        title="AI Daily Briefing Assistant",
        version=resolved_settings.app_version,
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.state.settings = resolved_settings
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def trace_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        trace_id = request.headers.get("X-Trace-Id", uuid4().hex)
        otel_trace = trace_id_from_span()
        if otel_trace:
            trace_id = otel_trace
        bind_trace_id(trace_id)
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers["X-Trace-Id"] = trace_id
        return response

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint — no authentication required."""
        return {
            "status": "healthy",
            "version": resolved_settings.app_version,
        }

    app.include_router(briefing_router)
    app.include_router(consent_router)
    app.include_router(preferences_router)
    app.include_router(export_router)
    app.include_router(dlq_router)
    app.mount("/metrics", make_asgi_app())

    return app


app = create_app()
