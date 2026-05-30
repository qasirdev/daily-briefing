"""Tests for Prometheus metrics."""

from backend.metrics import (
    AGENT_EXECUTION_DURATION,
    BRIEFING_GENERATION_DURATION,
    observe_agent_execution,
    record_briefing_generation,
    record_dlq_event,
    record_llm_tokens,
    record_security_violation,
)


def test_custom_metrics_registered() -> None:
    sample = BRIEFING_GENERATION_DURATION.labels(status="success", degraded="false")
    assert sample._labelvalues == ("success", "false")
    assert AGENT_EXECUTION_DURATION._name == "agent_execution_duration_seconds"


def test_record_helpers_do_not_raise() -> None:
    with observe_agent_execution(agent_id="task", role="doer"):
        pass
    record_llm_tokens(agent_id="focus", model="test", tokens=10)
    record_dlq_event(reason="circuit_breaker", agent_id="focus")
    record_security_violation(violation_type="injection", agent_id="critic")
    record_briefing_generation(status="success", degraded=False, duration_seconds=0.5)
