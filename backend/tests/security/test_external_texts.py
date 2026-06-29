"""External text collection for security scanning."""

from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope, ExecutionMetadata
from backend.security.external_texts import collect_external_texts, collect_mcp_external_texts


def _envelope(agent_id: str, result: dict[str, object]) -> AgentResultEnvelope:
    return AgentResultEnvelope(
        agent_id=agent_id,
        canonical_role="doer",
        status="success",
        result=result,
        metadata=ExecutionMetadata(
            execution_ms=1,
            tokens_used=0,
            model_used="none",
            prompt_version="v2.0.0",
            trace_id="f" * 32,
            data_classification="internal",
        ),
    )


def test_collect_mcp_external_texts_includes_task_and_calendar() -> None:
    state: BriefingGraphState = {
        "task_result": _envelope("task", {"tasks": [{"title": "Ship feature"}]}),
        "calendar_result": _envelope("calendar", {"events": [{"summary": "Standup"}]}),
    }
    texts = collect_mcp_external_texts(state)
    assert set(texts) == {"task", "calendar"}
    assert "Ship feature" in texts["task"]
    assert "Standup" in texts["calendar"]


def test_collect_external_texts_includes_focus_when_present() -> None:
    state: BriefingGraphState = {
        "task_result": _envelope("task", {"tasks": []}),
        "focus_result": _envelope("focus", {"plan": "Deep work block"}),
    }
    texts = collect_external_texts(state)
    assert "focus" in texts
    assert "Deep work block" in texts["focus"]
