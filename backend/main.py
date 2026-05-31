"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from slowapi.middleware import SlowAPIMiddleware

from backend.api.v1.briefing import router as briefing_router
from backend.api.v1.consent import router as consent_router
from backend.api.v1.dlq import router as dlq_router
from backend.api.v1.export import router as export_router
from backend.api.v1.preferences import router as preferences_router
from backend.health.router import router as health_router
from backend.logging_config import bind_trace_id, configure_logging, get_logger
from backend.security.rate_limit import register_rate_limiting
from backend.settings import Settings, get_settings
from backend.shutdown import ShutdownCoordinator
from backend.telemetry import configure_telemetry, trace_id_from_span

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — configure logging and telemetry on startup."""
    settings = get_settings()
    configure_logging(debug=settings.app_debug)
    configure_telemetry(settings)
    if "asyncpg" in settings.database_url:
        from backend.db.session import init_engine

        init_engine(settings)

    coordinator: ShutdownCoordinator = app.state.shutdown
    try:
        coordinator.register_signal_handlers()
    except NotImplementedError:
        logger.info("signal_handlers_unavailable")

    logger.info("application_started", app_env=settings.app_env, version=settings.app_version)
    yield
    await coordinator.shutdown(app)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    resolved_settings = settings or get_settings()

    app = FastAPI(
        title="AI Daily Briefing Assistant",
        version=resolved_settings.app_version,
        lifespan=lifespan,
    )
    app.state.shutdown = ShutdownCoordinator()
    app.state.settings = resolved_settings
    register_rate_limiting(app)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def shutdown_gate_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        coordinator: ShutdownCoordinator = request.app.state.shutdown
        if not coordinator.accepting_requests:
            return JSONResponse(status_code=503, content={"detail": "Server shutting down"})
        await coordinator.track_request()
        try:
            return await call_next(request)
        finally:
            await coordinator.release_request()

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

    app.include_router(health_router)
    app.include_router(briefing_router)
    app.include_router(consent_router)
    app.include_router(preferences_router)
    app.include_router(export_router)
    app.include_router(dlq_router)
    app.mount("/metrics", make_asgi_app())

    return app


app = create_app()
