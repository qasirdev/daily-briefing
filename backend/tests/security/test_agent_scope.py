"""Agent scope boundary tests."""

from backend.security.token_budget import AGENT_TOKEN_BUDGETS


def test_token_budgets_defined_for_core_agents() -> None:
    assert set(AGENT_TOKEN_BUDGETS) == {
        "task",
        "calendar",
        "focus",
        "verification",
        "adversarial",
        "critic",
    }


def test_focus_agent_has_largest_budget() -> None:
    assert AGENT_TOKEN_BUDGETS["focus"] >= AGENT_TOKEN_BUDGETS["task"]
    assert AGENT_TOKEN_BUDGETS["focus"] >= AGENT_TOKEN_BUDGETS["calendar"]
