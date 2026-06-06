"""ABAC policy evaluation for per-action authorization (Gap #128)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import structlog

from backend.consent.store import ConsentStore, consent_store
from backend.schemas.consent import ConsentService

logger = structlog.get_logger()

ActionType = Literal["mcp_tool", "credential_issue", "data_read", "data_write"]


class PolicyDeniedError(Exception):
    """Raised when ABAC policy evaluation denies an action."""


class PolicyUnavailableError(Exception):
    """Raised when policy evaluation cannot complete (fail-closed)."""


@dataclass(frozen=True, slots=True)
class PolicyContext:
    """Attributes evaluated for each authorization decision."""

    user_id: str
    agent_id: str
    service: ConsentService
    action: ActionType
    resource: str
    scope: list[str]


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Result of a real-time policy evaluation."""

    allowed: bool
    reason: str = ""


class PolicyEngine:
    """Evaluate ABAC rules using fresh consent state (no stale cache)."""

    def __init__(self, consent: ConsentStore | None = None) -> None:
        self._consent = consent or consent_store

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        """Evaluate authorization for a single action."""
        if not context.user_id.strip():
            return PolicyDecision(allowed=False, reason="user_id required")

        if not self._consent.has_valid_consent(context.user_id, context.service):
            return PolicyDecision(allowed=False, reason="consent_missing_or_expired")

        record = self._consent.get_active(context.user_id, context.service)
        if record is None:
            return PolicyDecision(allowed=False, reason="consent_record_not_found")

        if context.agent_id and record.agent_id != context.agent_id:
            return PolicyDecision(
                allowed=False,
                reason=f"agent_mismatch: expected {record.agent_id}, got {context.agent_id}",
            )

        if context.action == "data_write":
            write_scopes = {"tasks.write", "calendar.write", "tasks.update"}
            if not any(scope in write_scopes for scope in record.scope):
                return PolicyDecision(allowed=False, reason="write_scope_not_granted")

        if context.scope:
            missing = [scope for scope in context.scope if scope not in record.scope]
            if missing:
                return PolicyDecision(
                    allowed=False,
                    reason=f"scope_missing: {', '.join(missing)}",
                )

        logger.debug(
            "policy_evaluated",
            user_id=context.user_id,
            service=context.service,
            action=context.action,
            allowed=True,
        )
        return PolicyDecision(allowed=True, reason="policy_allow")

    def evaluate_or_raise(self, context: PolicyContext) -> PolicyDecision:
        """Evaluate policy and raise PolicyDeniedError when denied."""
        try:
            decision = self.evaluate(context)
        except Exception as exc:
            msg = f"Policy evaluation failed: {exc}"
            raise PolicyUnavailableError(msg) from exc

        if not decision.allowed:
            msg = f"Policy denied: {decision.reason}"
            raise PolicyDeniedError(msg)
        return decision


policy_engine = PolicyEngine()
