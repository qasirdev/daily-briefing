"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration validated at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_version: str = "0.1.0"

    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_primary_model: str = "openai/gpt-4o-mini"
    llm_fallback_model: str = "local/llama-3-8b"
    local_llm_enabled: bool = False
    local_llm_base_url: str = "http://localhost:8080/v1"

    database_url: str = "postgresql://briefing:briefing@localhost:5432/briefing"
    postgres_mcp_host: str = "localhost"
    postgres_mcp_port: int = 5433
    calendar_mcp_host: str = "localhost"
    calendar_mcp_port: int = 5434

    token_budget_max: int = 16_000
    graph_timeout_seconds: int = 60

    otel_exporter_otlp_endpoint: str = "http://localhost:4317"

    jwt_secret_key: str = Field(
        default="dev-only-jwt-secret-change-in-production-0123456789abcdef",
        min_length=32,
    )

    cors_origins: str = "http://localhost:3000,http://localhost"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> Self:
        if self.app_env == "production" and self.jwt_secret_key.startswith("dev-only"):
            msg = "JWT_SECRET_KEY must be set to a secure value in production"
            raise ValueError(msg)
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
