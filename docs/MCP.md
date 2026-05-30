# Model Context Protocol (MCP) Integrations — AI Daily Briefing Assistant

**Version:** 1.5.0 | **Last Updated:** May 2026

---

## Overview

The AI Daily Briefing Assistant uses the Model Context Protocol (MCP) to provide agents with controlled access to external tools and data sources. MCP servers run as separate processes and communicate via local TCP.

```
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              MCP Client Manager                      │    │
│  │  ┌──────────────┐        ┌──────────────────────┐   │    │
│  │  │ pg_mcp_client│        │ calendar_mcp_client  │   │    │
│  │  └──────┬───────┘        └──────────┬───────────┘   │    │
│  └─────────┼───────────────────────────┼───────────────┘    │
│            │                           │                     │
└────────────┼───────────────────────────┼─────────────────────┘
             │ TCP :5443                 │ TCP :5444
             ▼                           ▼
┌────────────────────┐        ┌─────────────────────────┐
│ PostgreSQL MCP     │        │ Google Calendar MCP     │
│ Server             │        │ Server                  │
└─────────┬──────────┘        └───────────┬─────────────┘
          │                               │
          ▼                               ▼
┌────────────────────┐        ┌─────────────────────────┐
│ PostgreSQL DB      │        │ Google Calendar API     │
└────────────────────┘        └─────────────────────────┘
```

---

## PostgreSQL MCP Server

### Purpose
Provides the Task Agent and Orchestrator with structured access to the application database.

### Configuration

```yaml
# mcp/postgres/config.yaml
server:
  host: localhost
  port: 5443 # default 5433
  
database:
  url: ${DATABASE_URL}
  pool_size: 5
  
security:
  rls_enabled: true
  read_only_role: task_agent_reader
  
tools:
  - list_tables
  - query
  - insert
```

### Available Tools

#### `list_tables`

Returns available tables the agent can query.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "tables": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "schema": { "type": "string" },
          "row_count": { "type": "integer" }
        }
      }
    }
  }
}
```

**Example Response:**
```json
{
  "tables": [
    { "name": "tasks", "schema": "public", "row_count": 42 },
    { "name": "user_preferences", "schema": "public", "row_count": 1 },
    { "name": "dlq_events", "schema": "public", "row_count": 3 }
  ]
}
```

#### `query`

Executes a read-only SQL query with parameterized inputs.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "sql": {
      "type": "string",
      "description": "SQL SELECT query"
    },
    "params": {
      "type": "object",
      "description": "Query parameters (prevents SQL injection)"
    },
    "user_id": {
      "type": "string",
      "description": "User ID for RLS enforcement"
    }
  },
  "required": ["sql", "user_id"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "rows": {
      "type": "array",
      "items": { "type": "object" }
    },
    "row_count": { "type": "integer" },
    "execution_ms": { "type": "integer" }
  }
}
```

**Example Request:**
```json
{
  "sql": "SELECT id, title, priority, due_date FROM tasks WHERE user_id = :user_id AND status = :status ORDER BY priority DESC",
  "params": { "status": "pending" },
  "user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### `insert`

Inserts a record (restricted to DLQ and specific tables).

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "table": {
      "type": "string",
      "enum": ["dlq_events", "user_preferences"]
    },
    "data": {
      "type": "object",
      "description": "Record to insert"
    },
    "user_id": {
      "type": "string"
    }
  },
  "required": ["table", "data", "user_id"]
}
```

### Security Controls

| Control | Implementation |
|---|---|
| **Row Level Security** | All queries filtered by `user_id` |
| **Read-Only Role** | Task Agent uses `task_agent_reader` role |
| **Allowlisted Tables** | Only `tasks`, `user_preferences`, `dlq_events` accessible |
| **Parameterized Queries** | SQL injection prevention |
| **Query Timeout** | 30 second maximum |
| **Result Limit** | Maximum 1000 rows per query |

### Error Handling

```python
class MCPError(Exception):
    """Base MCP error."""
    pass

class MCPTimeoutError(MCPError):
    """MCP operation timed out."""
    pass

class MCPPermissionError(MCPError):
    """Permission denied by MCP server."""
    pass

# Agent usage
try:
    result = await pg_mcp.query(sql="SELECT ...", user_id=user_id)
except MCPTimeoutError:
    return AgentResultEnvelope(
        status="escalated",
        escalation=EscalationPayload(
            reason="mcp_timeout",
            target_agent="orchestrator",
            context="PostgreSQL MCP query exceeded 30s timeout"
        )
    )
```

---

## Google Calendar MCP Server

### Purpose
Provides the Calendar Agent with read-only access to user calendar data.

### Configuration

```yaml
# mcp/calendar/config.yaml
server:
  host: localhost
  port: 5444  #default: 5434

google:
  client_id: ${GOOGLE_CLIENT_ID}
  client_secret: ${GOOGLE_CLIENT_SECRET}
  redirect_uri: http://localhost:3000/api/auth/callback/google
  
security:
  ssrf_allowlist:
    - "*.googleapis.com"
  consent_ttl_hours: 4
  scopes:
    - "https://www.googleapis.com/auth/calendar.readonly"

tools:
  - list_calendars
  - get_events
```

### Available Tools

#### `list_calendars`

Returns calendars the user has granted access to.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "user_id": { "type": "string" }
  },
  "required": ["user_id"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "calendars": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "primary": { "type": "boolean" }
        }
      }
    }
  }
}
```

#### `get_events`

Fetches calendar events for a date range.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "user_id": { "type": "string" },
    "calendar_id": { 
      "type": "string",
      "default": "primary"
    },
    "date": {
      "type": "string",
      "format": "date",
      "description": "ISO date (YYYY-MM-DD)"
    },
    "time_min": {
      "type": "string",
      "format": "date-time"
    },
    "time_max": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["user_id", "date"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "events": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "summary": { "type": "string" },
          "description": { "type": "string" },
          "start": { "type": "string", "format": "date-time" },
          "end": { "type": "string", "format": "date-time" },
          "attendees": {
            "type": "array",
            "items": { "type": "string" }
          },
          "location": { "type": "string" }
        }
      }
    }
  }
}
```

**Example Response:**
```json
{
  "events": [
    {
      "id": "abc123",
      "summary": "Team Standup",
      "description": "Daily sync with engineering team",
      "start": "2026-05-29T09:00:00Z",
      "end": "2026-05-29T09:30:00Z",
      "attendees": ["alice@example.com", "bob@example.com"],
      "location": "Conference Room A"
    }
  ]
}
```

### Security Controls

| Control | Implementation |
|---|---|
| **SSRF Defense** | Outbound requests restricted to `*.googleapis.com` |
| **OAuth Scope** | `calendar.readonly` only |
| **Consent TTL** | 4-hour living contract |
| **Input Sanitization** | Event descriptions scanned for prompt injection |
| **Token Storage** | Encrypted at rest, never logged |

### Consent Flow

```
┌────────┐     ┌─────────────┐     ┌────────────────┐
│ Agent  │────▶│ Calendar MCP│────▶│ Token Store    │
│ Request│     │             │     │                │
└────────┘     └──────┬──────┘     └───────┬────────┘
                      │                     │
                      │ Token expired?      │
                      │◄────────────────────┘
                      │
               ┌──────▼──────┐
               │ Return      │
               │ consent_    │
               │ required    │
               └──────┬──────┘
                      │
                      ▼
               ┌─────────────┐
               │ Frontend    │
               │ shows       │
               │ ConsentModal│
               └─────────────┘
```

### Error Handling

| Error | Response | Retry |
|---|---|---|
| `consent_required` | Surface modal to user | After consent |
| `token_expired` | Trigger refresh | Auto-retry once |
| `rate_limited` | Backoff | After cooldown |
| `ssrf_blocked` | Log security event | Never |
| `timeout` | Route to DLQ | Never |

---

## MCP Client Implementation

### Client Manager

```python
from dataclasses import dataclass
from typing import Protocol
import httpx

class MCPClient(Protocol):
    async def call_tool(self, tool_name: str, args: dict) -> dict:
        ...

@dataclass
class MCPClientConfig:
    host: str
    port: int
    timeout: float = 30.0

class MCPClientManager:
    """Manages MCP client connections."""
    
    def __init__(self):
        self._clients: dict[str, MCPClient] = {}
    
    async def initialize(self, configs: dict[str, MCPClientConfig]):
        for name, config in configs.items():
            self._clients[name] = await self._create_client(config)
    
    def get_client(self, name: str) -> MCPClient:
        return self._clients[name]
    
    async def close(self):
        for client in self._clients.values():
            await client.close()
```

### Agent Usage Pattern

```python
async def calendar_agent_node(state: BriefingGraphState) -> AgentResultEnvelope:
    """Calendar Agent — Tool Operator role."""
    
    mcp = mcp_manager.get_client("calendar")
    
    try:
        result = await mcp.call_tool(
            "get_events",
            {
                "user_id": state["user_id"],
                "date": state["requested_at"].date().isoformat(),
            }
        )
        
        return AgentResultEnvelope(
            agent_id="calendar",
            canonical_role="tool_operator",
            status="success",
            result=result,
            metadata=ExecutionMetadata(
                execution_ms=result.get("execution_ms", 0),
                tokens_used=0,
                model_used="none",
                prompt_version="v1.5.0",
                trace_id=state["trace_id"],
                data_classification="confidential_pii",
            ),
        )
        
    except MCPConsentRequired:
        return AgentResultEnvelope(
            status="escalated",
            escalation=EscalationPayload(
                reason="consent_required",
                target_agent="orchestrator",
                context="Google Calendar consent expired"
            )
        )
```

---

## Observability

### MCP Metrics

| Metric | Type | Labels |
|---|---|---|
| `mcp_call_duration_seconds` | Histogram | `server`, `tool`, `status` |
| `mcp_call_total` | Counter | `server`, `tool`, `status` |
| `mcp_errors_total` | Counter | `server`, `tool`, `error_type` |
| `mcp_active_connections` | Gauge | `server` |

### Tracing

All MCP calls include OpenTelemetry span context:

```python
from opentelemetry import trace

tracer = trace.get_tracer("mcp.client")

async def call_tool(self, tool_name: str, args: dict) -> dict:
    with tracer.start_as_current_span(
        f"mcp.{self.server_name}.{tool_name}",
        attributes={
            "mcp.server": self.server_name,
            "mcp.tool": tool_name,
        }
    ) as span:
        result = await self._execute(tool_name, args)
        span.set_attribute("mcp.execution_ms", result.get("execution_ms", 0))
        return result
```

---

*MCP Documentation — Version 1.5.0 — May 2026*
