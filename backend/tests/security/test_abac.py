"""ABAC enforcement tests (Gap #20)."""

from __future__ import annotations

import pytest

from backend.security.abac import assert_allowed_action, assert_resource_owner


def test_assert_resource_owner_allows_matching_user() -> None:
    assert_resource_owner(
        actor_user_id="user-1",
        resource_user_id="user-1",
        resource="tasks",
    )


def test_assert_resource_owner_blocks_cross_user_access() -> None:
    with pytest.raises(PermissionError, match="Cross-user"):
        assert_resource_owner(
            actor_user_id="user-1",
            resource_user_id="user-2",
            resource="tasks",
        )


def test_assert_allowed_action_requires_permission() -> None:
    assert_allowed_action(action="calendar:read", permissions=("calendar:read", "tasks:read"))
    with pytest.raises(PermissionError, match="not permitted"):
        assert_allowed_action(action="calendar:write", permissions=("calendar:read",))
