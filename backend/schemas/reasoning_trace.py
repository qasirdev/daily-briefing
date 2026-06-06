"""Reasoning trace schemas for HITL observability (Gaps #67-68)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

HitlLayerId = Literal[
    "input",
    "planning",
    "review",
    "revision",
    "execution",
    "monitoring",
    "override",
    "feedback",
]


class ReasoningTraceEntry(BaseModel):
    """Single reasoning step exposed to operators."""

    model_config = ConfigDict(strict=True)

    agent_id: str
    hitl_layer: HitlLayerId
    summary: str = Field(..., min_length=1, max_length=500)
    status: Literal["success", "failure", "escalated", "awaiting_human"] = "success"
    tokens_used: int = Field(default=0, ge=0)
    execution_ms: int = Field(default=0, ge=0)


class ReasoningTraceResponse(BaseModel):
    """Collection of reasoning traces for a briefing run."""

    model_config = ConfigDict(strict=True)

    trace_id: str = Field(..., min_length=32, max_length=64)
    entries: list[ReasoningTraceEntry] = Field(default_factory=list)
    hitl_mode: Literal["human_on_the_loop", "human_in_the_loop"] = "human_on_the_loop"
