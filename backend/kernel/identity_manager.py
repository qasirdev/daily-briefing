"""User identity propagation and delegation tokens (Gaps #18, #118)."""

from __future__ import annotations

from typing import Literal

from backend.security.delegation import DelegationContext, issue_delegation, validate_delegation
from backend.security.vault import CredentialBroker

CredentialIntent = Literal["read_events", "read_tasks", "update_tasks"]


class IdentityManager:
    """Issues delegation contexts and JIT credentials on behalf of users."""

    def __init__(self, broker: CredentialBroker | None = None) -> None:
        self._broker = broker or CredentialBroker()

    def create_delegation(
        self,
        *,
        user_id: str,
        session_id: str,
        agent_id: str,
        intent: CredentialIntent,
        permissions: tuple[str, ...],
        parent_trace_id: str,
    ) -> DelegationContext:
        return issue_delegation(
            user_id=user_id,
            session_id=session_id,
            agent_id=agent_id,
            intent=intent,
            permissions=permissions,
            parent_trace_id=parent_trace_id,
        )

    def assert_delegation(
        self,
        context: DelegationContext,
        *,
        required_intent: CredentialIntent | None = None,
        required_permission: str | None = None,
    ) -> None:
        validate_delegation(
            context,
            required_intent=required_intent,
            required_permission=required_permission,
        )

    async def get_credential(
        self,
        *,
        user_id: str,
        service: Literal["google_calendar", "supabase"],
        intent: CredentialIntent,
    ) -> object:
        return await self._broker.get_credential(user_id=user_id, service=service, intent=intent)
