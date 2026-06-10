"""Agent OS Kernel component tests."""

from __future__ import annotations

from backend.kernel import IdentityManager, MemoryManager, Scheduler, SecurityMonitor, ToolManager
from backend.security.delegation import issue_delegation


def test_scheduler_includes_consensus_phases_when_enabled() -> None:
    pipeline = Scheduler().pipeline(consensus_enabled=True)
    assert "verification" in pipeline
    assert "critic" in pipeline
    assert pipeline.index("critic") > pipeline.index("adversarial")


def test_scheduler_omits_consensus_when_disabled() -> None:
    pipeline = Scheduler().pipeline(consensus_enabled=False)
    assert "verification" not in pipeline
    assert "consensus" not in pipeline


def test_identity_manager_issues_delegation() -> None:
    manager = IdentityManager()
    context = manager.create_delegation(
        user_id="user-1",
        session_id="sess-1",
        agent_id="calendar",
        intent="read_events",
        permissions=("calendar:read",),
        parent_trace_id="d" * 32,
    )
    manager.assert_delegation(context, required_intent="read_events")
    assert context.agent_id == "calendar"


def test_tool_manager_and_memory_manager_construct() -> None:
    assert ToolManager() is not None
    assert MemoryManager() is not None
    assert SecurityMonitor.alert_coverage() == 1.0


def test_issue_delegation_audit_trail() -> None:
    context = issue_delegation(
        user_id="user-2",
        session_id="sess-2",
        agent_id="task",
        intent="read_tasks",
        permissions=("tasks:read",),
        parent_trace_id="e" * 32,
    )
    assert context.intent == "read_tasks"
