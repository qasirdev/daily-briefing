"""LLM response models."""

from pydantic import BaseModel, ConfigDict, Field


class LLMResponse(BaseModel):
    """Normalized response from any LLM provider."""

    model_config = ConfigDict(strict=True, frozen=True)

    content: str = Field(..., min_length=1)
    model_used: str = Field(..., min_length=1)
    tokens_used: int = Field(..., ge=0, le=128_000)
    latency_ms: int = Field(..., ge=0, le=300_000)
