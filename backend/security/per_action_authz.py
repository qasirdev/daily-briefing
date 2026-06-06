"""Per-action authorization layer (Gaps #52, #128)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import structlog

from backend.observability.metrics import record_per_action_authz
from backend.schemas.consent import ConsentService, coerce_consent_service
from backend.security.policy_engine import (
    PolicyContext,
    PolicyDecision,
    PolicyDeniedError,
    PolicyEngine,
    policy_engine,
)

logger = structlog.get_logger()

CredentialIntent = Literal["read_events", "read_tasks", "update_tasks"]


@dataclass(frozen=True, slots=True)
class ActionRequest:
    """Authorization request for a single agent action."""

    user_id: str
    agent_id: str
    service: ConsentService
    action: Literal["mcp_tool", "credential_issue", "data_read", "data_write"]
    resource: str = ""
    scope: list[str] | None = None
    intent: CredentialIntent | None = None


INTENT_SCOPE_MAP: dict[CredentialIntent, list[str]] = {
    "read_events": ["calendar.readonly"],
    "read_tasks": ["tasks.read"],
    "update_tasks": ["tasks.write"],
}


class PerActionAuthorizer:
    """Authorize every MCP call and credential issuance in real time."""

    def __init__(self, engine: PolicyEngine | None = None) -> None:
        self._engine = engine or policy_engine

    def authorize(self, request: ActionRequest) -> PolicyDecision:
        """Run per-action authorization; records metric on outcome."""
        scope = list(request.scope or [])
        if request.intent is not None:
            scope = INTENT_SCOPE_MAP.get(request.intent, scope)

        context = PolicyContext(
            user_id=request.user_id,
            agent_id=request.agent_id,
            service=coerce_consent_service(request.service),
            action=request.action,
            resource=request.resource,
            scope=scope,
        )
        decision = self._engine.evaluate(context)
        outcome = "allow" if decision.allowed else "deny"
        record_per_action_authz(service=request.service, action=request.action, outcome=outcome)
        if not decision.allowed:
            logger.warning(
                "per_action_authz_denied",
                user_id=request.user_id,
                service=request.service,
                action=request.action,
                reason=decision.reason,
            )
        return decision

    def authorize_or_raise(self, request: ActionRequest) -> PolicyDecision:
        """Authorize and raise PolicyDeniedError when denied."""
        decision = self.authorize(request)
        if not decision.allowed:
            msg = f"Per-action authorization denied: {decision.reason}"
            raise PolicyDeniedError(msg)
        return decision


per_action_authorizer = PerActionAuthorizer()
