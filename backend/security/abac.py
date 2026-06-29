"""Attribute-based access control helpers (Gap #20).

PostgreSQL RLS enforces row isolation; this module validates user attributes
before memory and MCP operations at the application layer.
"""

from __future__ import annotations


def assert_resource_owner(*, actor_user_id: str, resource_user_id: str, resource: str) -> None:
    """Ensure the acting user may access a user-scoped resource."""
    if not actor_user_id or not resource_user_id:
        msg = f"Missing user identity for {resource} access"
        raise PermissionError(msg)
    if actor_user_id != resource_user_id:
        msg = f"Cross-user access denied for {resource}"
        raise PermissionError(msg)


def assert_allowed_action(*, action: str, permissions: tuple[str, ...]) -> None:
    """Ensure the delegation token grants the requested action."""
    if action not in permissions:
        msg = f"Action '{action}' not permitted by delegation token"
        raise PermissionError(msg)
