"""Task prioritization and agent invocation order (Gap #27)."""

from __future__ import annotations

from typing import Literal

AgentPhase = Literal[
    "orchestrator_route",
    "parallel_task_calendar",
    "input_security_gate",
    "focus",
    "verification",
    "adversarial",
    "critic",
    "consensus",
    "present",
]

DEFAULT_PIPELINE: tuple[AgentPhase, ...] = (
    "orchestrator_route",
    "parallel_task_calendar",
    "input_security_gate",
    "focus",
    "verification",
    "adversarial",
    "critic",
    "consensus",
    "present",
)


class Scheduler:
    """Exposes canonical agent invocation order for observability and tests."""

    def pipeline(self, *, consensus_enabled: bool = True) -> tuple[AgentPhase, ...]:
        if consensus_enabled:
            return DEFAULT_PIPELINE
        skip = {"verification", "adversarial", "consensus"}
        return tuple(phase for phase in DEFAULT_PIPELINE if phase not in skip)
