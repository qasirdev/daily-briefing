"""Graceful shutdown coordination for production deployments."""

from __future__ import annotations

import asyncio
import signal
import time
from typing import Any

from backend.logging_config import get_logger
from backend.telemetry import flush_telemetry

logger = get_logger(__name__)

SHUTDOWN_DRAIN_SECONDS = 30.0


class ShutdownCoordinator:
    """Track in-flight requests and drain on SIGTERM/SIGINT."""

    def __init__(self) -> None:
        self._active_requests = 0
        self._accepting = True
        self._force_exit = False
        self._lock = asyncio.Lock()

    @property
    def accepting_requests(self) -> bool:
        return self._accepting and not self._force_exit

    async def track_request(self) -> None:
        async with self._lock:
            self._active_requests += 1

    async def release_request(self) -> None:
        async with self._lock:
            self._active_requests = max(0, self._active_requests - 1)

    def register_signal_handlers(self) -> None:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._on_signal, sig)

    def _on_signal(self, sig: signal.Signals) -> None:
        if self._force_exit:
            raise SystemExit(1)
        self._accepting = False
        logger.warning("shutdown_signal_received", signal=sig.name)

    async def shutdown(self, app: Any) -> None:
        """Drain in-flight work, close clients, flush telemetry."""
        started = time.perf_counter()
        self._accepting = False
        deadline = time.perf_counter() + SHUTDOWN_DRAIN_SECONDS

        while self._active_requests > 0 and time.perf_counter() < deadline:
            await asyncio.sleep(0.1)

        if self._active_requests > 0:
            logger.warning(
                "shutdown_forced_with_active_requests",
                active_requests=self._active_requests,
            )

        mcp = getattr(app.state, "mcp_clients", None)
        if mcp is not None:
            try:
                await mcp.close()
            except Exception as exc:
                logger.warning("shutdown_mcp_close_failed", error=str(exc))

        flush_telemetry()
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info("shutdown_complete", elapsed_ms=elapsed_ms)
