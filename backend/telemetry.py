"""OpenTelemetry configuration and helpers."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SpanExporter

from backend.settings import Settings

_tracer: trace.Tracer | None = None
_telemetry_configured = False


def get_tracer() -> trace.Tracer:
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer("daily-briefing")
    return _tracer


def configure_telemetry(settings: Settings) -> None:
    """Configure OTLP tracing; continue without export if collector unavailable."""
    global _telemetry_configured, _tracer
    if _telemetry_configured:
        return

    resource = Resource.create(
        {"service.name": "daily-briefing", "service.version": settings.app_version},
    )
    provider = TracerProvider(resource=resource)

    exporter: SpanExporter | None = None
    if settings.otel_exporter_otlp_endpoint:
        try:
            exporter = OTLPSpanExporter(
                endpoint=settings.otel_exporter_otlp_endpoint,
                insecure=True,
            )
        except Exception as exc:  # noqa: BLE001 — telemetry must not block startup
            logging.getLogger(__name__).warning("otel_exporter_init_failed: %s", exc)

    if exporter is not None:
        provider.add_span_processor(BatchSpanProcessor(exporter))
    elif settings.app_debug:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer = get_tracer()
    _telemetry_configured = True


def flush_telemetry() -> None:
    """Flush pending span batches during shutdown."""
    provider = trace.get_tracer_provider()
    shutdown = getattr(provider, "shutdown", None)
    if callable(shutdown):
        shutdown()


def trace_id_from_span() -> str | None:
    span = trace.get_current_span()
    context = span.get_span_context()
    if not context.is_valid:
        return None
    return format(context.trace_id, "032x")


@contextmanager
def start_span(name: str, **attributes: str | int | float | bool) -> Iterator[trace.Span]:
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield span


@asynccontextmanager
async def start_async_span(
    name: str,
    **attributes: str | int | float | bool,
) -> AsyncIterator[trace.Span]:
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield span
