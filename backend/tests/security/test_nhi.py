"""Tests for Non-Human Identity (NHI) Registry (Gap #92-93)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.security.nhi_registry import NHIRecord, NHIRegistry, nhi_registry


@pytest.fixture
def test_registry_path(tmp_path: Path) -> Path:
    """Provide an isolated registry file path for each test."""
    return tmp_path / "nhi_registry_test.json"


def test_nhi_registry_registration(test_registry_path: Path) -> None:
    """Verify registration persists and retrieves correctly."""
    registry = NHIRegistry(registry_path=test_registry_path)

    record = NHIRecord(
        nhi_id="nhi_test_agent_v1",
        agent_name="test",
        version="1.0.0",
        capability_level="low",
        risk_level="low",
        lifecycle="ephemeral",
        access_model="static",
        registered_by="pytest",
    )

    registry.register(record)
    retrieved = registry.get("nhi_test_agent_v1")

    assert retrieved is not None
    assert retrieved.agent_name == "test"
    assert retrieved.capability_level == "low"
    assert retrieved.lifecycle == "ephemeral"
    assert test_registry_path.exists()


def test_nhi_duplicate_registration_fails(test_registry_path: Path) -> None:
    """Verify duplicate NHI IDs raise ValueError."""
    registry = NHIRegistry(registry_path=test_registry_path)

    record = NHIRecord(
        nhi_id="nhi_duplicate_v1",
        agent_name="duplicate",
        version="1.0.0",
        capability_level="low",
        risk_level="low",
        lifecycle="persistent",
        access_model="static",
        registered_by="pytest",
    )

    registry.register(record)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(record)


def test_nhi_dynamic_credentials_flag() -> None:
    """Verify dynamic credential requirement detection."""
    high_capability_dynamic = NHIRecord(
        nhi_id="nhi_calendar_v2",
        agent_name="calendar",
        version="2.0.0",
        capability_level="high",
        risk_level="high",
        lifecycle="ephemeral",
        access_model="dynamic",
        registered_by="system",
    )

    assert high_capability_dynamic.requires_dynamic_credentials is True

    low_capability_static = NHIRecord(
        nhi_id="nhi_task_v2",
        agent_name="task",
        version="2.0.0",
        capability_level="low",
        risk_level="low",
        lifecycle="persistent",
        access_model="static",
        registered_by="system",
    )

    assert low_capability_static.requires_dynamic_credentials is False


def test_nhi_list_all(test_registry_path: Path) -> None:
    """Verify list_all returns every registered record."""
    registry = NHIRegistry(registry_path=test_registry_path)

    agent_names = ("alpha", "beta", "gamma")
    for agent_name in agent_names:
        registry.register(
            NHIRecord(
                nhi_id=f"nhi_{agent_name}_v1",
                agent_name=agent_name,
                version="1.0.0",
                capability_level="low",
                risk_level="low",
                lifecycle="persistent",
                access_model="static",
                registered_by="pytest",
            ),
        )

    all_records = registry.list_all()
    assert len(all_records) == 3
    assert all(isinstance(record, NHIRecord) for record in all_records)


def test_nhi_id_pattern_validation() -> None:
    """Verify NHI ID pattern validation."""
    NHIRecord(
        nhi_id="nhi_test_v1",
        agent_name="test",
        version="1.0.0",
        capability_level="low",
        risk_level="low",
        lifecycle="persistent",
        access_model="static",
        registered_by="pytest",
    )

    NHIRecord(
        nhi_id="nhi_long_agent_name_v99",
        agent_name="long_agent_name",
        version="99.0.0",
        capability_level="low",
        risk_level="low",
        lifecycle="persistent",
        access_model="static",
        registered_by="pytest",
    )

    with pytest.raises(ValidationError):
        NHIRecord(
            nhi_id="invalid_pattern",
            agent_name="test",
            version="1.0.0",
            capability_level="low",
            risk_level="low",
            lifecycle="persistent",
            access_model="static",
            registered_by="pytest",
        )

    with pytest.raises(ValidationError):
        NHIRecord(
            nhi_id="nhi_test_1",
            agent_name="test",
            version="1.0.0",
            capability_level="low",
            risk_level="low",
            lifecycle="persistent",
            access_model="static",
            registered_by="pytest",
        )


def test_nhi_external_connections_tracking() -> None:
    """Verify external connections are tracked for posture assessment."""
    record = NHIRecord(
        nhi_id="nhi_external_v1",
        agent_name="external",
        version="1.0.0",
        capability_level="high",
        risk_level="high",
        lifecycle="ephemeral",
        access_model="dynamic",
        registered_by="pytest",
        external_connections=[
            "google_calendar_mcp",
            "slack_mcp",
            "github_api",
        ],
    )

    assert len(record.external_connections) == 3
    assert "google_calendar_mcp" in record.external_connections


def test_production_registry_has_five_agents() -> None:
    """Verify singleton registry bootstraps all five production agents."""
    records = nhi_registry.list_all()
    nhi_ids = {record.nhi_id for record in records}

    assert len(records) == 5
    assert nhi_ids == {
        "nhi_task_agent_v1",
        "nhi_calendar_agent_v1",
        "nhi_focus_agent_v1",
        "nhi_critic_agent_v1",
        "nhi_orchestrator_v1",
    }

    calendar = nhi_registry.get("nhi_calendar_agent_v1")
    assert calendar is not None
    assert calendar.hitl_required is True
    assert calendar.requires_dynamic_credentials is True
