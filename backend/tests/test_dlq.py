"""Tests for DLQ store and API."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from backend.dlq.store import DLQStore
from backend.main import create_app
from backend.schemas.dlq import DLQEvent
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.settings import Settings


@pytest.fixture
def store() -> DLQStore:
    return DLQStore()


def _event(reason: str = "circuit_breaker") -> DLQEvent:
    return DLQEvent(
        request_id="req-1",
        user_id="user-1",
        agent_id="focus",
        reason=reason,  # type: ignore[arg-type]
        trace_id="f" * 32,
        envelope=AgentResultEnvelope(
            agent_id="focus",
            canonical_role="planner",
            status="escalated",
            metadata=ExecutionMetadata(
                execution_ms=1,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id="f" * 32,
                data_classification="internal",
            ),
        ),
    )


def test_dlq_store_add_and_list(store: DLQStore) -> None:
    event = store.add(_event())
    listed = store.list_events()
    assert len(listed) == 1
    assert listed[0].id == event.id


def test_security_violation_not_retryable(store: DLQStore) -> None:
    event = store.add(_event("security_violation_detected"))
    allowed, message = store.can_retry(event)
    assert allowed is False
    assert "cannot be retried" in message


def test_dlq_api_requires_admin_key() -> None:
    settings = Settings(admin_api_key="secret-admin")
    client = TestClient(create_app(settings))
    response = client.get("/api/v1/dlq")
    assert response.status_code == 403


def test_dlq_api_lists_events() -> None:
    from backend.dlq import store as dlq_module

    dlq_module.dlq_store.add(_event())
    settings = Settings(admin_api_key="secret-admin")
    client = TestClient(create_app(settings))
    response = client.get("/api/v1/dlq", headers={"X-Admin-Key": "secret-admin"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1


def test_dlq_retry_rejects_security_event() -> None:
    from backend.dlq import store as dlq_module

    event = dlq_module.dlq_store.add(_event("security_violation_detected"))
    settings = Settings(admin_api_key="secret-admin")
    client = TestClient(create_app(settings))
    response = client.post(
        f"/api/v1/dlq/{event.id}/retry",
        headers={"X-Admin-Key": "secret-admin"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_dlq_persist_does_not_raise_on_mcp_failure(store: DLQStore) -> None:
    postgres = AsyncMock()
    postgres.insert = AsyncMock(side_effect=RuntimeError("mcp down"))
    event = _event()
    persisted = await store.persist(event, postgres=postgres)
    assert persisted.id == event.id
