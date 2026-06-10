"""Non-Human Identity (NHI) Registry for AI agents.

Tracks all agents as non-human identities with unique IDs, capability
assessment, and security posture tracking (Gap #92-93).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_REGISTRY_PATH = Path("backend/security/nhi_registry.json")


class NHIRecord(BaseModel):
    """Non-human identity record for AI agents."""

    model_config = ConfigDict(strict=True, frozen=True)

    nhi_id: str = Field(
        ...,
        pattern=r"^nhi_[a-z_]+_v\d+$",
        description="Unique identifier following nhi_{name}_v{version} pattern",
    )
    agent_name: str = Field(
        ...,
        description="Human-readable agent name (e.g., calendar, task, focus)",
    )
    version: str = Field(
        ...,
        description="Semantic version (e.g., 1.0.0)",
    )
    capability_level: Literal["low", "high"] = Field(
        ...,
        description="Low = read/query only; High = planning, execution, external writes",
    )
    risk_level: Literal["low", "high"] = Field(
        ...,
        description="Low = non-sensitive data; High = PII, external APIs, financial",
    )
    lifecycle: Literal["ephemeral", "persistent"] = Field(
        ...,
        description="Ephemeral = per-request; Persistent = long-lived service",
    )
    access_model: Literal["static", "dynamic"] = Field(
        ...,
        description="Static = fixed credentials; Dynamic = JIT token issuance",
    )
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Registration timestamp",
    )
    registered_by: str = Field(
        ...,
        description="Engineer or system that registered this NHI",
    )
    external_connections: list[str] = Field(
        default_factory=list,
        description="MCP servers or APIs this agent connects to",
    )
    secrets_manager: str = Field(
        default="env",
        description="How secrets are managed: env, vault, none",
    )
    hitl_required: bool = Field(
        default=False,
        description="Whether human-in-the-loop approval is required",
    )

    @property
    def requires_dynamic_credentials(self) -> bool:
        """Return True when agent needs JIT credentials from vault."""
        return self.access_model == "dynamic" and self.capability_level == "high"


class NHIRegistry:
    """Registry for tracking non-human identities with JSON persistence."""

    def __init__(self, registry_path: str | Path = DEFAULT_REGISTRY_PATH) -> None:
        """Initialize NHI registry and load from file."""
        self.registry_path = Path(registry_path)
        self._registry: dict[str, NHIRecord] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        """Load registry from JSON file or start empty if missing."""
        if not self.registry_path.exists():
            self._registry = {}
            return

        with self.registry_path.open(encoding="utf-8") as file:
            data = json.load(file)
            self._registry = {
                nhi_id: NHIRecord.model_validate_json(json.dumps(record))
                for nhi_id, record in data.items()
            }

    def register(self, record: NHIRecord) -> None:
        """Register a new NHI and persist to disk."""
        if record.nhi_id in self._registry:
            msg = f"NHI {record.nhi_id} already registered"
            raise ValueError(msg)

        self._registry[record.nhi_id] = record
        self._save_registry()

    def ensure_registered(self, record: NHIRecord) -> None:
        """Register an NHI only when it is not already present."""
        if record.nhi_id not in self._registry:
            self.register(record)

    def get(self, nhi_id: str) -> NHIRecord | None:
        """Return an NHI record by ID."""
        return self._registry.get(nhi_id)

    def list_all(self) -> list[NHIRecord]:
        """Return all registered NHI records."""
        return list(self._registry.values())

    def _save_registry(self) -> None:
        """Persist registry to JSON file with timestamps preserved."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        with self.registry_path.open("w", encoding="utf-8") as file:
            json.dump(
                {
                    nhi_id: record.model_dump(mode="json")
                    for nhi_id, record in self._registry.items()
                },
                file,
                indent=2,
            )


def _default_agent_records() -> list[NHIRecord]:
    """Return the five production agent NHI records."""
    return [
        NHIRecord(
            nhi_id="nhi_task_agent_v1",
            agent_name="task",
            version="1.0.0",
            capability_level="low",
            risk_level="low",
            lifecycle="persistent",
            access_model="static",
            registered_by="system",
            external_connections=["postgres_mcp"],
            secrets_manager="env",
        ),
        NHIRecord(
            nhi_id="nhi_calendar_agent_v1",
            agent_name="calendar",
            version="1.0.0",
            capability_level="high",
            risk_level="high",
            lifecycle="ephemeral",
            access_model="dynamic",
            registered_by="system",
            external_connections=["google_calendar_mcp"],
            secrets_manager="env",
            hitl_required=True,
        ),
        NHIRecord(
            nhi_id="nhi_focus_agent_v1",
            agent_name="focus",
            version="1.0.0",
            capability_level="high",
            risk_level="low",
            lifecycle="persistent",
            access_model="static",
            registered_by="system",
            external_connections=[],
            secrets_manager="none",
        ),
        NHIRecord(
            nhi_id="nhi_critic_agent_v1",
            agent_name="critic",
            version="1.0.0",
            capability_level="low",
            risk_level="low",
            lifecycle="persistent",
            access_model="static",
            registered_by="system",
            external_connections=[],
            secrets_manager="none",
        ),
        NHIRecord(
            nhi_id="nhi_orchestrator_v1",
            agent_name="orchestrator",
            version="1.0.0",
            capability_level="high",
            risk_level="low",
            lifecycle="persistent",
            access_model="static",
            registered_by="system",
            external_connections=[],
            secrets_manager="none",
        ),
    ]


def bootstrap_default_agents(registry: NHIRegistry) -> None:
    """Ensure all production agents are registered idempotently."""
    for record in _default_agent_records():
        registry.ensure_registered(record)


nhi_registry = NHIRegistry()
bootstrap_default_agents(nhi_registry)
