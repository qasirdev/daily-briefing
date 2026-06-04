# Engineering Standards — AI Daily Briefing Assistant

**Version:** 1.6.0 | **Last Updated:** June 2026

---

## Twelve-Factor App Compliance

This project adheres to the [Twelve-Factor App](https://12factor.net/) methodology for building modern, scalable applications.

| Factor | Implementation | Status |
|---|---|---|
| **I. Codebase** | Single Git repository, multiple deploys via branches | ⬜ Specified |
| **II. Dependencies** | Explicit via `pyproject.toml` (uv) and `package.json` (npm) | ⬜ Specified |
| **III. Config** | Environment variables, `.env` files, never in code | ⬜ Specified |
| **IV. Backing Services** | Supabase PostgreSQL, Google Calendar API as attached resources | ⬜ Specified |
| **V. Build, Release, Run** | Docker multi-stage build, CI/CD pipeline | ⬜ Specified |
| **VI. Processes** | Stateless processes, state in PostgreSQL | ⬜ Specified |
| **VII. Port Binding** | Self-contained via uvicorn/next.js, exposed through Nginx | ⬜ Specified |
| **VIII. Concurrency** | Process model via supervisord, horizontal scaling ready | ⬜ Specified |
| **IX. Disposability** | Graceful SIGTERM handling, fast startup | ⬜ Specified |
| **X. Dev/Prod Parity** | Docker Compose for local, same image in production | ⬜ Specified |
| **XI. Logs** | Structured JSON to stdout, collected externally | ⬜ Specified |
| **XII. Admin Processes** | One-off tasks via management commands | ⬜ Specified |

---

## Technology Stack & Versions

### Backend (Python)

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Runtime (stable LTS with PEP 695 generics) |
| uv | >=0.5.0 | Package manager (replaces pip/poetry) |
| FastAPI | >=0.115.0 | Web framework |
| Pydantic | >=2.11.0 | Data validation (v2 with Rust core) |
| uvicorn | >=0.32.0 | ASGI server |
| langgraph | >=0.4.0 | Multi-agent orchestration |
| openai | >=1.40.0 | LLM SDK (OpenAI-compatible) |
| litellm | >=1.50.0 | LLM routing/fallback |
| tenacity | >=9.0.0 | Retry logic |
| structlog | >=24.4.0 | Structured logging |
| opentelemetry-api | >=1.28.0 | Observability |
| pyjwt[crypto] | >=2.9.0 | JWT handling |
| nh3 | >=0.2.14 | HTML sanitization |
| httpx | >=0.28.0 | Async HTTP client |
| asyncpg | >=0.30.0 | PostgreSQL driver |

### Frontend (TypeScript)

| Dependency | Version | Purpose |
|---|---|---|
| Node.js | 22.x LTS | Runtime |
| Next.js | 16.x | React framework |
| React | 19.x | UI library (hooks: use, useTransition, useOptimistic, useActionState) |
| TypeScript | 5.6+ | Type safety |
| Tailwind CSS | 4.x | Styling |
| Zod | >=3.23.0 | Runtime validation |
| DOMPurify | >=3.2.0 | XSS protection |

### Infrastructure

| Component | Version | Purpose |
|---|---|---|
| Docker | 27.x | Containerization |
| Nginx | 1.27.x | Reverse proxy |
| Supervisord | 4.2.x | Process manager |
| PostgreSQL | 16.x (Supabase) | Primary database (Supavisor :6543) |

---

## Configuration Management

### Environment Variables

All configuration is injected via environment variables. Never hardcode secrets.

```bash
# .env.example — Document all required variables

# Application
APP_ENV=development|staging|production
APP_DEBUG=false
APP_SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Database — Supabase Supavisor (port 6543)
DATABASE_URL=postgresql+asyncpg://postgres.[ref]:[password]@...pooler.supabase.com:6543/postgres?sslmode=require
MCP_POSTGRES_URL=postgresql://postgres.[ref]:[password]@...pooler.supabase.com:6543/postgres?sslmode=require

# MCP — stdio (Option 1 default) or http (legacy TCP mock servers)
MCP_TRANSPORT=stdio

# MCP HTTP fallback only (when MCP_TRANSPORT=http)
POSTGRES_MCP_HOST=localhost
POSTGRES_MCP_PORT=5443
CALENDAR_MCP_HOST=localhost
CALENDAR_MCP_PORT=5444

# Google Calendar OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8088
CALENDAR_ID=primary

# LLM
OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_PRIMARY_MODEL=openai/gpt-4o-mini
LOCAL_LLM_ENABLED=false
LOCAL_LLM_BASE_URL=http://localhost:8080/v1

# Observability / security
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-64>
CORS_ORIGINS=http://localhost:3010,http://127.0.0.1:3010,http://localhost
```

**Supabase URL rules:** use port **6543** (Supavisor pooler); URL-encode `$` in passwords as `%24`; no quotes around `DATABASE_URL` / `MCP_POSTGRES_URL`; no inline `#` comments on values (breaks parsing).

### Production Configuration

Use `.env.production.example` for deploy templates.

| Variable | Production requirement |
|---|---|
| `APP_ENV` | `production` |
| `APP_DEBUG` | `false` (startup validation fails if true) |
| `JWT_SECRET_KEY` | Strong secret — no dev/default markers |
| `ADMIN_API_KEY` | Required for DLQ admin API |
| `OPENROUTER_API_KEY` | Required unless `LOCAL_LLM_ENABLED=true` |
| `CORS_ORIGINS` | Production frontend domain(s) only |

Rate limits: briefing `10/min`, export `5/hour`, other API `60/min` per IP.

### Pydantic Settings Validation

```python
"""Application settings with environment variable validation.

Loads and validates all configuration from environment variables using
Pydantic Settings. All settings are immutable after initialization.
"""

from typing import Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.
    
    All settings are validated on startup. Invalid configuration will
    raise ValidationError and prevent application from starting.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        frozen=True,  # Immutable after creation
    )
    
    # Application
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environment name for configuration selection",
    )
    app_debug: bool = Field(
        default=False,
        description="Enable debug mode (must be False in production)",
    )
    app_secret_key: str = Field(
        ...,
        min_length=32,
        description="Secret key for session encryption",
    )
    
    # Database
    database_url: PostgresDsn = Field(
        ...,
        description="PostgreSQL connection URL (Supabase Supavisor port 6543)",
    )
    database_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum database connection pool size",
    )
    
    # LLM
    openrouter_api_key: str = Field(
        ...,
        min_length=10,
        description="OpenRouter API key for LLM access",
    )
    llm_primary_model: str = Field(
        default="openai/gpt-4o-mini",
        description="Primary LLM model identifier",
    )
    
    # Security
    jwt_secret_key: str = Field(
        ...,
        min_length=64,
        description="JWT signing key (64+ character hex string)",
    )


# Singleton instance — validated once at startup
settings = Settings()
```

---

## Code Quality Standards

### Python

| Tool | Configuration | Purpose |
|---|---|---|
| `ruff` | `pyproject.toml` | Linting + formatting (replaces black/isort/flake8) |
| `mypy` | `strict=true` | Static type checking |
| `pytest` | `pytest.ini` | Testing |
| `pytest-cov` | 80% minimum | Coverage |

```toml
# pyproject.toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM", "TCH"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
```

### Python Coding Standards

#### Type Hints (Mandatory)

**All functions must have complete type annotations for parameters and return values.**

```python
# ✅ CORRECT — Modern type hints (Python 3.10+, required in 3.14+)
def find_user(user_id: int) -> str | None:
    """Find user by ID, return name or None if not found."""
    return users.get(user_id)

def process_items(items: list[str]) -> dict[str, int]:
    """Count occurrences of each item."""
    return {item: items.count(item) for item in set(items)}

# ❌ INCORRECT — Old-style type hints (avoid in all new code)
from typing import Optional, List, Dict

def find_user_old(user_id: int) -> Optional[str]:  # Use str | None instead
    return users.get(user_id)

def process_items_old(items: List[str]) -> Dict[str, int]:  # Use list[str], dict[str, int]
    return {item: items.count(item) for item in set(items)}
```

**Modern Type Hint Standards:**

- ✅ Use `str | None` instead of `Optional[str]`
- ✅ Use `list[T]` instead of `List[T]`
- ✅ Use `dict[K, V]` instead of `Dict[K, V]`
- ✅ Use `tuple[T, ...]` instead of `Tuple[T, ...]`
- ✅ Use PEP 695 generics for Python 3.14+: `def func[T](x: T) -> T`
- ❌ Never use bare `Any` without justification
- ❌ Never use untyped function parameters or returns

#### PEP 695 Generics (Python 3.12+)

```python
# ✅ CORRECT — PEP 695 generic syntax (Python 3.12+)
def first[T](items: list[T]) -> T | None:
    """Return first item or None if list is empty."""
    return items[0] if items else None

class Box[T]:
    """Generic container for any type."""
    
    def __init__(self, value: T) -> None:
        """Initialize box with a value."""
        self.value = value
    
    def get(self) -> T:
        """Get the contained value."""
        return self.value

# ❌ AVOID — Old TypeVar syntax (legacy, but still works)
from typing import TypeVar, Generic

T = TypeVar("T")

def first_old(items: list[T]) -> T | None:
    return items[0] if items else None
```

#### Docstrings (Mandatory for All Definitions)

**Every function, class, method, and module must have a docstring.**

```python
"""Module for user authentication and session management.

Provides authentication via JWT tokens and session lifecycle management.
All functions require valid user credentials from the database.
"""

from typing import Literal


def authenticate_user(
    username: str,
    password: str,
) -> dict[str, str] | None:
    """Authenticate user with credentials and return session token.
    
    Validates username and password against database records using
    Argon2id hashing. Returns session details if successful.
    
    Args:
        username: User's login username (case-insensitive)
        password: Plain-text password (will be hashed for comparison)
    
    Returns:
        Dictionary with 'token' and 'expires_at' keys, or None if auth fails
        
    Example:
        >>> session = authenticate_user("alice", "secret123")
        >>> print(session["token"])
        'eyJhbGc...'
    """
    # Implementation here
    return {"token": "...", "expires_at": "..."}


class UserSession:
    """User session with JWT token and expiration tracking.
    
    Manages the lifecycle of an authenticated user session including
    token refresh, expiration checks, and cleanup.
    """
    
    def __init__(self, token: str, user_id: int) -> None:
        """Initialize session with token and user ID.
        
        Args:
            token: JWT token string
            user_id: Database user ID
        """
        self.token = token
        self.user_id = user_id
    
    def is_expired(self) -> bool:
        """Check if session token has expired.
        
        Returns:
            True if token is past expiration, False otherwise
        """
        # Implementation here
        return False
```

**Docstring Standards:**

- ✅ Module docstrings explain purpose and context
- ✅ Function docstrings use imperative mood ("Return X", not "Returns X")
- ✅ Include Args/Returns/Raises for complex functions
- ✅ Add Examples for public API functions
- ✅ Class docstrings describe purpose and usage
- ✅ Property docstrings explain what the property represents
- ❌ Never leave functions/classes without docstrings

#### Import Organization

**Imports must be organized in three groups, each sorted alphabetically:**

```python
# ✅ CORRECT — Organized imports
# Standard library (sorted)
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

# Third-party packages (sorted)
import httpx
import structlog
from pydantic import BaseModel, ConfigDict, Field

# Local imports (sorted)
from backend.graph.state import BriefingGraphState
from backend.schemas.envelope import AgentResultEnvelope

# ❌ INCORRECT — Mixed, unsorted imports
from backend.schemas.envelope import AgentResultEnvelope
import json
from pydantic import BaseModel
import structlog
from datetime import datetime
```

**Import Standards:**

- ✅ Standard library → Third-party → Local
- ✅ Each group sorted alphabetically
- ✅ Explicit imports from `typing` (e.g., `from typing import Literal`)
- ✅ One blank line between import groups
- ❌ Never use `import *`
- ❌ Never use relative imports beyond parent directory

#### Pydantic v2 Patterns

**Use ConfigDict, model_dump(), and Field descriptions for all models.**

```python
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr


# ✅ CORRECT — Pydantic v2 patterns
class User(BaseModel):
    """User account model with validated email and password.
    
    All fields are required unless explicitly marked with default values.
    Passwords are stored as SecretStr to prevent accidental logging.
    """
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,  # Immutable after creation
        from_attributes=True,  # Allow ORM object mapping
    )
    
    user_id: int = Field(
        ...,
        description="Database primary key",
        gt=0,
    )
    username: str = Field(
        ...,
        description="Unique username for login",
        min_length=3,
        max_length=50,
    )
    email: str = Field(
        ...,
        description="Validated email address",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    )
    password: SecretStr = Field(
        ...,
        description="Argon2id hashed password (never logged)",
    )
    role: Literal["user", "admin"] = Field(
        default="user",
        description="User role for authorization",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Account creation timestamp",
    )


# Example usage
user = User(
    user_id=123,
    username="alice",
    email="alice@example.com",
    password=SecretStr("hashed_password_here"),
)

# ✅ Pydantic v2 serialization
user_dict = user.model_dump()  # NOT .dict()
user_json = user.model_dump_json()  # NOT .json()

# ❌ INCORRECT — Pydantic v1 patterns (avoid in all new code)
class UserOld(BaseModel):
    user_id: int
    username: str
    
    class Config:  # Use model_config = ConfigDict(...) instead
        frozen = True
        orm_mode = True  # Use from_attributes=True instead

# user_dict = user_old.dict()  # Removed in Pydantic v2
# user_json = user_old.json()  # Removed in Pydantic v2
```

**Pydantic v2 Standards:**

- ✅ Use `model_config = ConfigDict(...)` instead of `class Config:`
- ✅ Use `model_dump()` instead of `.dict()`
- ✅ Use `model_dump_json()` instead of `.json()`
- ✅ Use `from_attributes=True` instead of `orm_mode=True`
- ✅ Use `SecretStr` for all passwords, API keys, tokens
- ✅ Add `Field(..., description="...")` to all model fields
- ✅ Use `frozen=True` for immutable models (envelopes, configs)
- ❌ Never use `class Config:` inner class
- ❌ Never call `.dict()` or `.json()` (removed in v2)

#### Testing Standards

**All test functions must have return type annotations and docstrings.**

```python
import pytest

from backend.security.nhi_registry import NHIRecord, NHIRegistry


def test_nhi_registry_registration() -> None:
    """Test NHI registration persists and retrieves correctly.
    
    Creates a temporary registry, registers an agent, and verifies
    retrieval returns the correct record with all fields intact.
    """
    registry = NHIRegistry(registry_path="test_registry.json")
    
    record = NHIRecord(
        nhi_id="nhi_test_v1",
        agent_name="test",
        version="1.0.0",
        capability_level="low",
        risk_level="low",
        lifecycle="persistent",
        access_model="static",
        registered_by="pytest",
    )
    
    registry.register(record)
    retrieved = registry.get("nhi_test_v1")
    
    assert retrieved is not None
    assert retrieved.agent_name == "test"


@pytest.mark.asyncio
async def test_async_function() -> None:
    """Test async function with proper await handling.
    
    Validates that async operations complete successfully and
    return expected results.
    """
    result = await some_async_function()
    assert result == "expected"
```

**Testing Standards:**

- ✅ All test functions use `-> None` return type
- ✅ Test docstrings explain what is being validated
- ✅ Descriptive test names: `test_<what>_<condition>_<expected>`
- ✅ Use `@pytest.mark.asyncio` for async tests
- ✅ Use pytest fixtures for common setup
- ✅ Use `pytest.raises(Exception)` for validation errors
- ❌ Never use bare `assert` without specific type checking

#### Async/Await Patterns

**Use async/await for all I/O operations (database, HTTP, MCP).**

```python
import asyncio

import httpx


async def fetch_user_data(user_id: int) -> dict[str, str]:
    """Fetch user data from external API.
    
    Args:
        user_id: User ID to fetch
        
    Returns:
        Dictionary with user data
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        response.raise_for_status()
        return response.json()


async def fetch_multiple_users(user_ids: list[int]) -> list[dict[str, str]]:
    """Fetch multiple users concurrently.
    
    Args:
        user_ids: List of user IDs to fetch
        
    Returns:
        List of user data dictionaries
    """
    # Concurrent execution with asyncio.gather
    results = await asyncio.gather(
        *[fetch_user_data(user_id) for user_id in user_ids],
        return_exceptions=True,  # Don't fail entire batch on one error
    )
    
    # Filter out exceptions
    return [result for result in results if isinstance(result, dict)]
```

**Async Standards:**

- ✅ Use `async def` for all async functions
- ✅ Use `async with` for async context managers
- ✅ Use `asyncio.gather()` for concurrent execution
- ✅ Use `await` on all coroutines (never leave dangling)
- ✅ Use `return_exceptions=True` in gather for error handling
- ❌ Never block the event loop with synchronous I/O

### TypeScript

| Tool | Configuration | Purpose |
|---|---|---|
| `eslint` | `eslint.config.mjs` | Linting |
| `prettier` | `.prettierrc` | Formatting |
| `tsc` | `strict: true` | Type checking |
| `vitest` | `vitest.config.ts` | Testing |

```json
// tsconfig.json (key settings)
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noImplicitReturns": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true
  }
}
```

---

## Resilience Patterns

### Retry Logic with Tenacity

```python
"""LLM API client with automatic retry on transient failures.

Uses tenacity for exponential backoff retry logic on HTTP errors.
"""

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
)
async def call_llm_api(messages: list[dict[str, str]]) -> dict[str, str]:
    """Call LLM API with automatic retry on transient failures.
    
    Retries up to 3 times with exponential backoff (2s, 4s, 8s, ..., max 30s)
    on HTTP 5xx errors and timeouts. Client errors (4xx) fail immediately.
    
    Args:
        messages: List of chat messages with 'role' and 'content' keys
        
    Returns:
        Dictionary with LLM response containing 'content' key
        
    Raises:
        HTTPStatusError: On 4xx client errors (not retried)
        TimeoutException: After all retries exhausted
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            json={"model": settings.llm_primary_model, "messages": messages},
            headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
        )
        response.raise_for_status()
        return response.json()
```

### Circuit Breaker in LangGraph

```python
"""LangGraph circuit breaker for token budget and retry limits.

Prevents runaway agent execution by enforcing hard limits on token
usage and revision counts. Failed requests route to DLQ for analysis.
"""

from langgraph.graph import END, StateGraph

from backend.graph.state import BriefingGraphState

# Hard limits — exceeding these triggers circuit breaker
TOKEN_BUDGET_HARD_LIMIT = 50_000
MAX_REVISIONS = 2


def should_circuit_break(state: BriefingGraphState) -> bool:
    """Circuit break on budget exceeded or max revisions.
    
    Checks if agent execution should be terminated due to:
    - Token budget exceeded (prevents denial-of-wallet)
    - Max revisions exceeded (prevents infinite loops)
    
    Args:
        state: Current graph state with token and revision counts
        
    Returns:
        True if circuit breaker should trigger, False otherwise
    """
    return (
        state["total_tokens"] > TOKEN_BUDGET_HARD_LIMIT
        or state["revision_count"] > MAX_REVISIONS
    )


# Configure circuit breaker in graph
graph = StateGraph(BriefingGraphState)
graph.add_conditional_edges(
    "critic",
    should_circuit_break,
    {True: "dlq_handler", False: "orchestrator"},
)
```

### Rate Limiting

```python
"""API rate limiting with SlowAPI per-IP limits.

Prevents abuse by limiting request frequency per IP address.
Returns 429 Too Many Requests with Retry-After header on limit exceeded.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


@app.post("/api/v1/briefing/generate")
@limiter.limit("10/minute")
async def generate_briefing(request: Request) -> dict[str, str]:
    """Generate daily briefing with rate limiting.
    
    Limited to 10 requests per minute per IP address. Exceeding this
    limit returns 429 status with Retry-After header.
    
    Args:
        request: FastAPI request object (used for rate limit key)
        
    Returns:
        Dictionary with briefing content and metadata
        
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    # Implementation here
    return {"briefing": "...", "status": "success"}
```

---

## Graceful Shutdown (Factor IX: Disposability)

```python
"""Graceful shutdown handler for FastAPI with signal handling.

Ensures all resources are properly cleaned up on SIGTERM, including
database connections and MCP clients. Prevents data loss during shutdown.
"""

import asyncio
import signal
from contextlib import asynccontextmanager

from fastapi import FastAPI

shutdown_event = asyncio.Event()


def handle_sigterm(signum: int, frame: object) -> None:
    """Handle SIGTERM for graceful shutdown.
    
    Triggered by Docker/Kubernetes stop commands. Sets shutdown event
    to initiate cleanup sequence.
    
    Args:
        signum: Signal number (SIGTERM=15)
        frame: Current stack frame
    """
    shutdown_event.set()


signal.signal(signal.SIGTERM, handle_sigterm)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI application lifecycle.
    
    Handles startup (initialize pools) and shutdown (cleanup) phases.
    Ensures resources are properly released on termination.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    await initialize_db_pool()
    await initialize_mcp_clients()
    
    yield
    
    # Shutdown
    await close_db_pool()
    await close_mcp_clients()


app = FastAPI(lifespan=lifespan)
```

---

## Structured Logging (Factor XI: Logs)

```python
"""Structured JSON logging configuration with structlog.

All logs are emitted as JSON to stdout for collection by external
log aggregation systems (e.g., Grafana Loki, ELK stack).
"""

import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage example
logger.info(
    "briefing_generated",
    user_id=user_id,
    trace_id=trace_id,
    execution_ms=execution_ms,
    tokens_used=tokens_used,
)
```

---

## Database Connection Pooling

```python
"""PostgreSQL connection pool management with asyncpg.

Maintains a pool of reusable database connections to avoid
connection overhead on every query. Pool size is configurable
via DATABASE_POOL_SIZE environment variable.
"""

import asyncpg
from contextlib import asynccontextmanager

pool: asyncpg.Pool | None = None


async def initialize_db_pool() -> None:
    """Initialize database connection pool on startup.
    
    Creates a connection pool with configurable size (default 10).
    Pool is stored in global variable for application-wide access.
    
    Raises:
        ConnectionError: If database connection fails
    """
    global pool
    pool = await asyncpg.create_pool(
        dsn=str(settings.database_url),
        min_size=5,
        max_size=settings.database_pool_size,
        max_inactive_connection_lifetime=300,
    )


async def close_db_pool() -> None:
    """Close database connection pool on shutdown.
    
    Ensures all connections are properly released and closed.
    Called automatically during FastAPI shutdown.
    """
    global pool
    if pool is not None:
        await pool.close()
        pool = None


@asynccontextmanager
async def get_db_connection():
    """Acquire database connection from pool.
    
    Context manager that automatically returns connection to pool
    after use. Handles connection errors and retries automatically.
    
    Yields:
        asyncpg.Connection: Database connection from pool
        
    Example:
        >>> async with get_db_connection() as conn:
        ...     result = await conn.fetch("SELECT * FROM users")
    """
    if pool is None:
        raise RuntimeError("Database pool not initialized")
    
    async with pool.acquire() as conn:
        yield conn
```

---

## Docker Multi-Stage Build

```dockerfile
# Stage 1: Build frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --frozen-lockfile
COPY frontend/ ./
RUN npm run build

# Stage 2: Build backend
FROM python:3.12-slim AS backend-builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Stage 3: Production
FROM python:3.12-slim AS production
WORKDIR /app

# Install nginx and supervisord
RUN apt-get update && apt-get install -y nginx supervisor && rm -rf /var/lib/apt/lists/*

# Copy built artifacts
COPY --from=frontend-builder /app/frontend/.next/standalone ./frontend/
COPY --from=backend-builder /app/.venv ./.venv

# Copy configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 80
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

---

*Engineering Standards — Version 1.6.0 — June 2026*
