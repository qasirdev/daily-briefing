"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlencode, urlparse, urlunparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

GOOGLE_OAUTH_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_CALENDAR_OAUTH_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


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
    llm_openrouter_models: str = ""
    llm_openrouter_route: str = "fallback"
    llm_fallback_model: str = "local/llama-3-8b"
    local_llm_enabled: bool = False
    local_llm_base_url: str = "http://localhost:8080/v1"
    local_llm_model_id: str = "local/llama-3-8b"

    google_oauth_authorize_url: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8088"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""
    calendar_id: str = "primary"

    database_url: str = "postgresql://briefing:briefing@localhost:5432/briefing"
    mcp_postgres_url: str = ""
    mcp_transport: Literal["http", "stdio"] = "stdio"
    postgres_mcp_host: str = "localhost"
    postgres_mcp_port: int = 5443
    calendar_mcp_host: str = "localhost"
    calendar_mcp_port: int = 5444

    token_budget_max: int = 16_000
    graph_timeout_seconds: int = 60
    enable_consensus_workflow: bool = False

    enable_prompt_caching: bool = True
    prompt_cache_warm_on_startup: bool = True
    prompt_cache_warm_interval_seconds: int = 240
    prompt_cache_warm_agents: str = "focus,critic,verification,adversarial"

    working_memory_token_limit: int = 16_000
    working_memory_max_snippets: int = 10
    semantic_memory_embedding_dim: int = 1536
    semantic_memory_search_top_k: int = 5
    enable_semantic_memory_retrieval: bool = True

    enable_procedural_memory: bool = True
    procedural_memory_top_k: int = 5
    enable_episodic_memory: bool = True
    episodic_memory_top_k: int = 5

    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    admin_api_key: str = ""

    jwt_secret_key: str = Field(
        default="dev-only-jwt-secret-change-in-production-0123456789abcdef",
        min_length=32,
    )

    cors_origins: str = "http://localhost:3000,http://localhost"

    @property
    def openrouter_model_chain(self) -> list[str]:
        """Ordered OpenRouter model list for in-request fallback routing."""
        if self.llm_openrouter_models.strip():
            seen: set[str] = set()
            chain: list[str] = []
            for part in self.llm_openrouter_models.split(","):
                model = part.strip()
                if model and model not in seen:
                    seen.add(model)
                    chain.append(model)
            if chain:
                return chain
        primary = self.llm_primary_model.strip()
        return [primary] if primary else []

    @model_validator(mode="after")
    def validate_production_secrets(self) -> Self:
        insecure_jwt_markers = ("dev-only", "change-me-in-production")
        if self.app_env == "production":
            if any(marker in self.jwt_secret_key for marker in insecure_jwt_markers):
                msg = "JWT_SECRET_KEY must be set to a secure value in production"
                raise ValueError(msg)
            if self.app_debug:
                msg = "APP_DEBUG must be false in production"
                raise ValueError(msg)
            if not self.admin_api_key:
                msg = "ADMIN_API_KEY is required in production"
                raise ValueError(msg)
            if not self.local_llm_enabled and not self.openrouter_api_key:
                msg = "OPENROUTER_API_KEY is required when LOCAL_LLM_ENABLED is false"
                raise ValueError(msg)
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def prompt_cache_warm_agent_list(self) -> list[str]:
        return [
            agent.strip() for agent in self.prompt_cache_warm_agents.split(",") if agent.strip()
        ]

    @property
    def resolved_mcp_postgres_url(self) -> str:
        if self.mcp_postgres_url:
            return self.mcp_postgres_url
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    @property
    def resolved_google_oauth_authorize_url(self) -> str:
        """OAuth authorize URL for the consent popup (built from client id when unset)."""
        if not self.google_client_id:
            return ""
        if self.google_oauth_authorize_url and "client_id=" in self.google_oauth_authorize_url:
            return self.google_oauth_authorize_url
        base = self.google_oauth_authorize_url or GOOGLE_OAUTH_AUTH_ENDPOINT
        parsed = urlparse(base)
        auth_base = urlunparse(parsed._replace(query="", fragment=""))
        params = urlencode(
            {
                "client_id": self.google_client_id,
                "redirect_uri": self.google_oauth_redirect_uri,
                "response_type": "code",
                "scope": GOOGLE_CALENDAR_OAUTH_SCOPE,
                "access_type": "offline",
                "prompt": "consent",
            },
        )
        return f"{auth_base}?{params}"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
