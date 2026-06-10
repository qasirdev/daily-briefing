# Non-Human Identity (NHI) Observability

## Overview

All AI agents are registered as non-human identities with unique IDs, audit trails, and security posture tracking.

## NHI Definition-of-Done (Pre-Merge Gate)

Before merging any PR that adds or modifies an agent:

1. [ ] Agent registered in `backend/security/nhi_registry.py`
2. [ ] Unique NHI ID assigned (format: `nhi_{agent_name}_{version}`)
3. [ ] Secrets/credentials consolidated (no hardcoded secrets)
4. [ ] External connections documented (MCP servers, APIs)
5. [ ] Risk assessment completed (capability × risk matrix)
6. [ ] Audit trail configured (all actions logged with NHI ID)

## NHI Registry Schema

```python
class NHIRecord(BaseModel):
    nhi_id: str  # e.g., "nhi_calendar_agent_v1"
    agent_name: str
    version: str
    capability_level: Literal["low", "high"]
    risk_level: Literal["low", "high"]
    lifecycle: Literal["ephemeral", "persistent"]
    access_model: Literal["static", "dynamic"]
    registered_at: datetime
    registered_by: str  # Engineer/system that registered
    external_connections: list[str]  # ["google_calendar_mcp", "postgres_mcp"]
    secrets_manager: str  # "vault", "env", "none"
```

## Capability × Risk Matrix

| Capability | Risk | HITL Required | Access Model | Example |
|------------|------|---------------|--------------|---------|
| Low | Low | No | Static | Task reader (read-only DB) |
| Low | High | Yes | Static | Finance data reader (PII) |
| High | Low | No | Dynamic | Style guide editor (non-sensitive) |
| High | High | Yes | Dynamic | Calendar agent (external API + PII) |

## Audit Requirements

Every NHI action must log:

- `nhi_id`
- `trace_id`
- `action` (tool_called, mcp_invoked, llm_requested)
- `target` (resource accessed)
- `outcome` (success, failure, escalated)
- `user_context` (on-behalf-of user)

## Registry Location

- **Implementation:** `backend/security/nhi_registry.py`
- **Persistence:** `backend/security/nhi_registry.json`
- **Tests:** `backend/tests/security/test_nhi.py`
