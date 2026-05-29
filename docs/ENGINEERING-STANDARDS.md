# Engineering Standards — AI Daily Briefing Assistant

**Version:** 1.5.0 | **Last Updated:** May 2026

---

## Twelve-Factor App Compliance

This project adheres to the [Twelve-Factor App](https://12factor.net/) methodology for building modern, scalable applications.

| Factor | Implementation | Status |
|---|---|---|
| **I. Codebase** | Single Git repository, multiple deploys via branches | ✅ |
| **II. Dependencies** | Explicit via `pyproject.toml` (uv) and `package.json` (npm) | ✅ |
| **III. Config** | Environment variables, `.env` files, never in code | ✅ |
| **IV. Backing Services** | PostgreSQL, Google Calendar API as attached resources | ✅ |
| **V. Build, Release, Run** | Docker multi-stage build, CI/CD pipeline | ✅ |
| **VI. Processes** | Stateless processes, state in PostgreSQL | ✅ |
| **VII. Port Binding** | Self-contained via uvicorn/next.js, exposed through Nginx | ✅ |
| **VIII. Concurrency** | Process model via supervisord, horizontal scaling ready | ✅ |
| **IX. Disposability** | Graceful SIGTERM handling, fast startup | ✅ |
| **X. Dev/Prod Parity** | Docker Compose for local, same image in production | ✅ |
| **XI. Logs** | Structured JSON to stdout, collected externally | ✅ |
| **XII. Admin Processes** | One-off tasks via management commands | ✅ |

---

## Technology Stack & Versions

### Backend (Python)

| Dependency | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Runtime |
| uv | >=0.5.0 | Package manager (replaces pip/poetry) |
| FastAPI | >=0.115.0 | Web framework |
| Pydantic | >=2.8.0 | Data validation |
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
| PostgreSQL | 16.x | Primary database |

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

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/briefing
DATABASE_POOL_SIZE=10
DATABASE_POOL_MAX_OVERFLOW=20

# LLM Configuration
OPENROUTER_API_KEY=<your-key>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
LLM_PRIMARY_MODEL=openai/gpt-4o-mini
LLM_FALLBACK_MODEL=local/llama-3-8b

# Local LLM (optional)
LOCAL_LLM_ENABLED=false
LOCAL_LLM_BASE_URL=http://localhost:8080/v1

# MCP Configuration
POSTGRES_MCP_HOST=localhost
POSTGRES_MCP_PORT=5433
CALENDAR_MCP_HOST=localhost
CALENDAR_MCP_PORT=5434

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=daily-briefing

# Security
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-64>
JWT_ALGORITHM=RS256
CORS_ORIGINS=http://localhost:3000
```

### Pydantic Settings Validation

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    app_env: str = Field(default="development", pattern=r"^(development|staging|production)$")
    app_debug: bool = False
    app_secret_key: str = Field(..., min_length=32)
    
    # Database
    database_url: PostgresDsn
    database_pool_size: int = Field(default=10, ge=1, le=100)
    
    # LLM
    openrouter_api_key: str = Field(..., min_length=10)
    llm_primary_model: str = "openai/gpt-4o-mini"
    
    # Security
    jwt_secret_key: str = Field(..., min_length=64)

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
```

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
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from httpx import HTTPStatusError, TimeoutException

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((HTTPStatusError, TimeoutException)),
)
async def call_llm_api(messages: list[dict]) -> dict:
    """Call LLM API with automatic retry on transient failures."""
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
from langgraph.graph import StateGraph, END

def should_circuit_break(state: BriefingGraphState) -> bool:
    """Circuit break on budget exceeded or max revisions."""
    return (
        state["total_tokens"] > TOKEN_BUDGET_HARD_LIMIT
        or state["revision_count"] > MAX_REVISIONS
    )

graph = StateGraph(BriefingGraphState)
graph.add_conditional_edges(
    "critic",
    should_circuit_break,
    {True: "dlq_handler", False: "orchestrator"},
)
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/briefing/generate")
@limiter.limit("10/minute")
async def generate_briefing(request: Request):
    """Generate daily briefing with rate limiting."""
    ...
```

---

## Graceful Shutdown (Factor IX: Disposability)

```python
import signal
import asyncio
from contextlib import asynccontextmanager

shutdown_event = asyncio.Event()

def handle_sigterm(signum, frame):
    """Handle SIGTERM for graceful shutdown."""
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_sigterm)

@asynccontextmanager
async def lifespan(app: FastAPI):
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

# Usage
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
import asyncpg
from contextlib import asynccontextmanager

pool: asyncpg.Pool | None = None

async def initialize_db_pool():
    global pool
    pool = await asyncpg.create_pool(
        dsn=str(settings.database_url),
        min_size=5,
        max_size=settings.database_pool_size,
        max_inactive_connection_lifetime=300,
    )

@asynccontextmanager
async def get_db_connection():
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

*Engineering Standards — Version 1.5.0 — May 2026*
