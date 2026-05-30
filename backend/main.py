"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.logging_config import bind_trace_id, configure_logging, get_logger
from backend.settings import Settings, get_settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — configure logging on startup."""
    settings = get_settings()
    configure_logging(debug=settings.app_debug)
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

    @app.get(
        "/api/v1/briefing/generate",
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
    )
    async def generate_briefing_placeholder() -> JSONResponse:
        """Placeholder until MVP 2 briefing generation is implemented."""
        return JSONResponse(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            content={"detail": "Briefing generation not yet implemented"},
        )

    return app


app = create_app()
