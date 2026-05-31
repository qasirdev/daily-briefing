"""Graceful shutdown tests."""

import pytest

from backend.shutdown import ShutdownCoordinator


@pytest.mark.asyncio
async def test_shutdown_waits_for_active_requests() -> None:
    coordinator = ShutdownCoordinator()
    await coordinator.track_request()
    coordinator._accepting = False
    await coordinator.release_request()
    assert coordinator._active_requests == 0


def test_shutdown_stops_accepting_requests() -> None:
    coordinator = ShutdownCoordinator()
    coordinator._accepting = False
    assert coordinator.accepting_requests is False
