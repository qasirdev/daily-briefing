"""Tests for Focus plan schema validation."""

from backend.agents.focus.schema import validate_focus_plan


def _valid_plan(**overrides: object) -> dict[str, object]:
    plan: dict[str, object] = {
        "summary": "Today's focus is completing the Q2 report before meetings.",
        "time_blocks": [
            {
                "start": "09:00",
                "end": "11:00",
                "activity": "Complete Q2 report analysis",
                "priority": "high",
                "type": "deep_work",
            },
        ],
        "top_priorities": [
            "Complete Q2 report analysis",
            "Review pending pull requests",
            "Prepare for afternoon meetings",
        ],
    }
    plan.update(overrides)
    return plan


def test_validate_focus_plan_accepts_valid_payload() -> None:
    assert validate_focus_plan(_valid_plan()) == []


def test_validate_focus_plan_rejects_missing_top_priorities() -> None:
    plan = _valid_plan()
    del plan["top_priorities"]
    errors = validate_focus_plan(plan)
    assert errors
    assert any("top_priorities" in error for error in errors)


def test_validate_focus_plan_rejects_invalid_time_format() -> None:
    plan = _valid_plan(
        time_blocks=[
            {
                "start": "9:00",
                "end": "11:00",
                "activity": "Complete Q2 report analysis",
                "priority": "high",
                "type": "deep_work",
            },
        ],
    )
    errors = validate_focus_plan(plan)
    assert errors
    assert any("start" in error for error in errors)


def test_validate_focus_plan_rejects_empty_time_blocks() -> None:
    errors = validate_focus_plan(_valid_plan(time_blocks=[]))
    assert errors
    assert any("time_blocks" in error for error in errors)
