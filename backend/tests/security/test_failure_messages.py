"""Failure message mapping tests."""

from backend.security.failure_messages import failure_message_for


def test_security_message_names_calendar_source() -> None:
    message = failure_message_for("security_violation_detected", source="calendar")
    assert message is not None
    assert "calendar data" in message


def test_security_message_names_task_source() -> None:
    message = failure_message_for("security_violation_detected", source="task")
    assert message is not None
    assert "task data" in message


def test_token_budget_message() -> None:
    message = failure_message_for("token_budget_exceeded")
    assert message is not None
    assert "token budget" in message.lower()
