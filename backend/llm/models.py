"""LLM response models."""

from pydantic import BaseModel, ConfigDict, Field


class LLMResponse(BaseModel):
    """Normalized response from any LLM provider."""

    model_config = ConfigDict(strict=True, frozen=True)

    content: str = Field(..., min_length=1)
    model_used: str = Field(..., min_length=1)
    tokens_used: int = Field(..., ge=0, le=128_000)
    prompt_tokens: int = Field(default=0, ge=0, le=128_000)
    completion_tokens: int = Field(default=0, ge=0, le=128_000)
    cost_usd: float = Field(default=0.0, ge=0.0)
    latency_ms: int = Field(..., ge=0, le=300_000)
