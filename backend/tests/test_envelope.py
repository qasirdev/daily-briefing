"""AgentResultEnvelope schema tests."""

import pytest
from pydantic import ValidationError

from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata


def _metadata(**overrides: object) -> ExecutionMetadata:
    base = {
        "execution_ms": 10,
        "tokens_used": 0,
        "model_used": "none",
        "prompt_version": "v1.5.0",
        "trace_id": "a" * 32,
        "data_classification": "internal",
    }
    base.update(overrides)
    return ExecutionMetadata(**base)  # type: ignore[arg-type]


def test_envelope_validates_success() -> None:
    envelope = AgentResultEnvelope(
        agent_id="task",
        canonical_role="doer",
        status="success",
        result={"tasks": []},
        metadata=_metadata(),
    )
    assert envelope.agent_id == "task"
    assert envelope.metadata.execution_ms == 10


def test_envelope_rejects_invalid_agent_id() -> None:
    with pytest.raises(ValidationError):
        AgentResultEnvelope(
            agent_id="Task-Agent",
            canonical_role="doer",
            status="success",
            result={"ok": True},
            metadata=_metadata(),
        )


def test_envelope_rejects_missing_result_on_success() -> None:
    with pytest.raises(ValidationError):
        AgentResultEnvelope(
            agent_id="task",
            canonical_role="doer",
            status="success",
            result=None,
            metadata=_metadata(),
        )


def test_envelope_is_frozen() -> None:
    envelope = AgentResultEnvelope(
        agent_id="task",
        canonical_role="doer",
        status="success",
        result={"tasks": []},
        metadata=_metadata(),
    )
    with pytest.raises(ValidationError):
        envelope.status = "failure"  # type: ignore[misc]
