# Backend AGENT.md — AI Daily Briefing Assistant

**Version:** 1.5.0 | **Last Updated:** May 2026

---

## Scope

This file governs all development within the FastAPI backend, including REST endpoints, LangGraph orchestration, MCP client integrations, and agent implementations.

---

## Technology Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Runtime |
| FastAPI | 0.115+ | Web framework |
| Pydantic | 2.8+ | Data validation |
| LangGraph | 0.4+ | Multi-agent orchestration |
| uvicorn | 0.32+ | ASGI server |
| structlog | 24.4+ | Structured logging |
| httpx | 0.28+ | Async HTTP client |
| asyncpg | 0.30+ | PostgreSQL driver |
| opentelemetry | 1.28+ | Observability |

---

## Architecture

```
backend/
├── AGENT.md                    # This file
├── main.py                     # FastAPI application entry point
├── settings.py                 # Pydantic Settings configuration
├── dependencies.py             # FastAPI dependency injection
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── briefing.py         # Briefing generation endpoints
│   │   ├── tasks.py            # Task management endpoints
│   │   ├── consent.py          # Consent management endpoints
│   │   └── export.py           # Data export endpoints
│   └── health.py               # Health check endpoints
├── agents/
│   ├── __init__.py
│   ├── AGENT.md                # Multi-agent rules
│   ├── orchestrator/
│   │   ├── AGENT.md
│   │   ├── __init__.py
│   │   └── node.py
│   ├── task/
│   │   ├── AGENT.md
│   │   ├── __init__.py
│   │   └── node.py
│   ├── calendar/
│   │   ├── AGENT.md
│   │   ├── __init__.py
│   │   └── node.py
│   ├── focus/
│   │   ├── AGENT.md
│   │   ├── __init__.py
│   │   └── node.py
│   └── critic/
│       ├── AGENT.md
│       ├── __init__.py
│       └── node.py
├── graph/
│   ├── __init__.py
│   ├── state.py                # BriefingGraphState definition
│   ├── builder.py              # Graph construction
│   └── nodes.py                # Node registry
├── mcp/
│   ├── __init__.py
│   ├── client.py               # MCP client base
│   ├── postgres.py             # PostgreSQL MCP client
│   └── calendar.py             # Google Calendar MCP client
├── llm/
│   ├── __init__.py
│   ├── router.py               # LLM routing with fallback
│   └── models.py               # LLM response models
├── schemas/
│   ├── __init__.py
│   ├── envelope.py             # AgentResultEnvelope
│   ├── briefing.py             # Briefing request/response
│   └── consent.py              # Consent models
├── security/
│   ├── __init__.py
│   ├── injection.py            # Prompt injection detection
│   └── sanitization.py         # Output sanitization
└── tests/
    ├── conftest.py
    ├── unit/
    ├── integration/
    └── security/
```

---

## Workflow Rules

| Rule | Behaviour |
|---|---|
| Agent Envelope Protocol | Every LangGraph node MUST return a validated `AgentResultEnvelope` |
| ReAct Loop Limits | The Critic Agent enforces a strict 2-cycle maximum revision loop |
| Escalation | Failures after 2 cycles, MCP timeouts, and injection detections route to DLQ |
| MCP Usage | Prefer MCP tool calls over custom repository wrappers |
| Type Safety | All public functions must have complete type annotations |
| Structured Logging | Use `structlog` for all logging; include `trace_id` in every log |
| Error Handling | Never catch generic `Exception`; always catch specific types |
| Backend verification gate | After every backend task, run the three commands below before marking done |

---

## Backend Verification Gate

After completing **every** backend task (implementation, refactor, or test changes), run these commands **in order** from the repository root:

```bash
uv run ruff check backend
uv run mypy backend
uv run pytest
```

| Step | Command | Pass criteria |
|---|---|---|
| 1 | `uv run ruff check backend` | Zero lint warnings |
| 2 | `uv run mypy backend` | Zero type errors |
| 3 | `uv run pytest` | All tests pass |

Do not mark a backend task complete or commit until all three pass. Capture test output in `logs/` when required by the epic verification gate.

---

## AgentResultEnvelope Schema

All agents must return this canonical envelope:

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from uuid import UUID
from datetime import datetime, timezone

class ExecutionMetadata(BaseModel):
    """Execution telemetry attached to every agent response."""
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    execution_ms: int = Field(..., ge=0, le=300_000)
    tokens_used: int = Field(..., ge=0, le=128_000)
    model_used: str = Field(..., min_length=1)
    prompt_version: str = Field(..., pattern=r"^v\d+\.\d+\.\d+$")
    trace_id: str = Field(..., min_length=32, max_length=64)
    data_classification: Literal["public", "internal", "confidential", "confidential_pii"]


class EscalationPayload(BaseModel):
    """Escalation details when agent cannot complete normally."""
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    reason: Literal[
        "security_violation_detected",
        "max_retries_exceeded", 
        "token_budget_exceeded",
        "mcp_timeout",
        "consent_required",
    ]
    target_agent: str = "orchestrator"
    context: str = ""


class AgentResultEnvelope(BaseModel):
    """Canonical envelope for all inter-agent communication."""
    
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")
    
    agent_id: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z_]+$")
    canonical_role: Literal["doer", "planner", "critic", "tool_operator", "supervisor"]
    status: Literal["success", "failure", "escalated"]
    result: dict | None = None
    metadata: ExecutionMetadata
    escalation: EscalationPayload | None = None
```

---

## LangGraph State

```python
from typing import TypedDict, Literal
from datetime import datetime, timezone

class BriefingGraphState(TypedDict):
    """Shared state across the agent graph."""
    
    # Request context
    user_id: str
    request_id: str
    trace_id: str
    requested_at: datetime
    
    # Agent outputs (accumulated)
    task_result: AgentResultEnvelope | None
    calendar_result: AgentResultEnvelope | None
    focus_result: AgentResultEnvelope | None
    critic_result: AgentResultEnvelope | None
    
    # Execution tracking
    current_agent: str
    revision_count: int
    total_tokens: int
    
    # Final output
    final_briefing: str | None
    status: Literal["pending", "success", "failure", "degraded"]
```

---

## Agent Node Pattern

```python
from backend.schemas import AgentResultEnvelope, ExecutionMetadata, EscalationPayload
from backend.graph.state import BriefingGraphState
from backend.llm.router import LLMRouter
from backend.mcp.postgres import PostgresMCPClient
import structlog
import time

logger = structlog.get_logger()

async def task_agent_node(
    state: BriefingGraphState,
    mcp: PostgresMCPClient,
) -> AgentResultEnvelope:
    """
    Task Agent — Doer role.
    
    Responsibilities:
    - Fetch pending tasks from PostgreSQL MCP
    - Prioritize tasks by due date and importance
    - Return structured task list
    
    Security:
    - Read-only database access
    - RLS enforced via user_id
    """
    start_time = time.perf_counter()
    
    logger.info(
        "task_agent_started",
        trace_id=state["trace_id"],
        user_id=state["user_id"],
    )
    
    try:
        # Fetch tasks via MCP
        result = await mcp.call_tool(
            "query",
            {
                "sql": """
                    SELECT id, title, priority, due_date, status
                    FROM tasks 
                    WHERE user_id = :user_id AND status = 'pending'
                    ORDER BY priority DESC, due_date ASC
                    LIMIT 20
                """,
                "user_id": state["user_id"],
            }
        )
        
        execution_ms = int((time.perf_counter() - start_time) * 1000)
        
        return AgentResultEnvelope(
            agent_id="task",
            canonical_role="doer",
            status="success",
            result={"tasks": result["rows"]},
            metadata=ExecutionMetadata(
                execution_ms=execution_ms,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id=state["trace_id"],
                data_classification="confidential",
            ),
        )
        
    except MCPTimeoutError:
        execution_ms = int((time.perf_counter() - start_time) * 1000)
        
        logger.error(
            "task_agent_mcp_timeout",
            trace_id=state["trace_id"],
        )
        
        return AgentResultEnvelope(
            agent_id="task",
            canonical_role="doer",
            status="escalated",
            escalation=EscalationPayload(
                reason="mcp_timeout",
                target_agent="orchestrator",
                context="PostgreSQL MCP query exceeded 30s timeout",
            ),
            metadata=ExecutionMetadata(
                execution_ms=execution_ms,
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id=state["trace_id"],
                data_classification="internal",
            ),
        )
```

---

## API Endpoint Pattern

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.schemas.briefing import BriefingRequest, BriefingResponse
from backend.graph.builder import build_briefing_graph
from backend.dependencies import get_current_user, get_mcp_clients
import structlog

router = APIRouter(prefix="/api/v1/briefing", tags=["briefing"])
limiter = Limiter(key_func=get_remote_address)
logger = structlog.get_logger()

@router.post("/generate", response_model=BriefingResponse)
@limiter.limit("10/minute")
async def generate_briefing(
    request: Request,
    body: BriefingRequest,
    user = Depends(get_current_user),
    mcp_clients = Depends(get_mcp_clients),
):
    """Generate a daily briefing for the authenticated user."""
    
    trace_id = request.state.trace_id
    
    logger.info(
        "briefing_generation_started",
        trace_id=trace_id,
        user_id=str(user.id),
    )
    
    graph = build_briefing_graph(mcp_clients)
    
    initial_state = BriefingGraphState(
        user_id=str(user.id),
        request_id=str(uuid.uuid4()),
        trace_id=trace_id,
        requested_at=datetime.now(timezone.utc),
        # ... other initial state
    )
    
    result = await graph.ainvoke(initial_state)
    
    return BriefingResponse(
        status=result["status"],
        briefing=result["final_briefing"] or "",
        metadata=result.get("metadata", {}),
    )
```

---

## MCP Client Usage

```python
from backend.mcp.client import MCPClient, MCPError, MCPTimeoutError

class PostgresMCPClient(MCPClient):
    """PostgreSQL MCP client with security controls."""
    
    ALLOWED_TABLES = {"tasks", "user_preferences", "dlq_events"}
    
    async def call_tool(self, tool_name: str, args: dict) -> dict:
        """Call MCP tool with validation."""
        
        # Validate table access
        if tool_name == "query":
            self._validate_query(args.get("sql", ""))
        
        if tool_name == "insert":
            table = args.get("table")
            if table not in self.ALLOWED_TABLES:
                raise MCPError(f"Access denied to table: {table}")
        
        return await super().call_tool(tool_name, args)
```

---

## Prompt Injection Detection

```python
import re
from dataclasses import dataclass

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"disregard\s+(your\s+)?(training|instructions?)",
    r"you\s+are\s+now\s+(in\s+)?debug\s+mode",
    r"\[\[SYSTEM\]\]",
    r"<\|im_start\|>",
    r"```system",
]

@dataclass
class InjectionDetectionResult:
    is_suspicious: bool
    matched_pattern: str | None
    confidence: float

class PromptInjectionDetector:
    """Detects potential prompt injection attempts."""
    
    def __init__(self):
        self._patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
    
    def detect(self, text: str) -> InjectionDetectionResult:
        """Scan text for injection patterns."""
        for pattern in self._patterns:
            if pattern.search(text):
                return InjectionDetectionResult(
                    is_suspicious=True,
                    matched_pattern=pattern.pattern,
                    confidence=0.9,
                )
        
        return InjectionDetectionResult(
            is_suspicious=False,
            matched_pattern=None,
            confidence=0.0,
        )
```

---

## Testing Requirements

### Unit Tests

```python
# tests/unit/test_agents.py
import pytest
from backend.agents.task.node import task_agent_node
from backend.schemas import AgentResultEnvelope

@pytest.mark.asyncio
async def test_task_agent_success(mock_mcp):
    """Task agent returns envelope with tasks."""
    mock_mcp.query.return_value = {"rows": [{"id": 1, "title": "Test"}]}
    
    result = await task_agent_node(mock_state, mock_mcp)
    
    assert isinstance(result, AgentResultEnvelope)
    assert result.status == "success"
    assert result.agent_id == "task"
    assert len(result.result["tasks"]) == 1

@pytest.mark.asyncio
async def test_task_agent_mcp_timeout(mock_mcp_timeout):
    """Task agent escalates on MCP timeout."""
    result = await task_agent_node(mock_state, mock_mcp_timeout)
    
    assert result.status == "escalated"
    assert result.escalation.reason == "mcp_timeout"
```

### Integration Tests

```python
# tests/integration/test_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_generate_briefing(client: AsyncClient, auth_headers):
    """Full briefing generation flow."""
    response = await client.post(
        "/api/v1/briefing/generate",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["success", "degraded"]
    assert "briefing" in data
```

---

## Error Handling

```python
from fastapi import HTTPException
from backend.schemas import AgentResultEnvelope

class BriefingGenerationError(Exception):
    """Base error for briefing generation."""
    pass

class SecurityViolationError(BriefingGenerationError):
    """Raised when security violation is detected."""
    pass

async def handle_agent_escalation(envelope: AgentResultEnvelope):
    """Handle agent escalation appropriately."""
    if envelope.escalation.reason == "security_violation_detected":
        raise SecurityViolationError(envelope.escalation.context)
    
    if envelope.escalation.reason == "consent_required":
        return {"status": "awaiting_consent", "context": envelope.escalation.context}
    
    # Route to DLQ
    await persist_to_dlq(envelope)
    raise BriefingGenerationError(f"Agent failed: {envelope.escalation.reason}")
```

---

*Backend AGENT.md — Version 1.5.0 — May 2026*
