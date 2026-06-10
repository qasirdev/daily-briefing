"""User-facing failure messages for briefing API responses."""

from __future__ import annotations

_SOURCE_LABELS: dict[str, str] = {
    "calendar": "calendar data",
    "task": "task data",
    "focus": "focus plan",
}


def failure_message_for(
    reason: str | None,
    *,
    source: str | None = None,
) -> str | None:
    """Map a DLQ / graph failure reason to a client-safe message."""
    if not reason:
        return None

    if reason == "security_violation_detected":
        if source in _SOURCE_LABELS:
            return f"Briefing blocked: suspected prompt injection in {_SOURCE_LABELS[source]}."
        return "Briefing blocked: suspected prompt injection in external data."

    messages: dict[str, str] = {
        "token_budget_exceeded": "Briefing stopped: token budget exceeded.",
        "max_retries_exceeded": "Briefing stopped: an agent exceeded its retry limit.",
        "mcp_timeout": "Briefing stopped: an external data source timed out.",
        "consent_expired": "Calendar consent expired. Re-authorize to continue.",
        "circuit_breaker": "Briefing stopped: pipeline circuit breaker triggered.",
        "unexpected_error": "Briefing stopped due to an unexpected error.",
        "verification_failed": "Briefing paused: focus plan failed verification.",
        "adversarial_concerns": "Briefing paused: adversarial review flagged concerns.",
    }
    return messages.get(reason)
