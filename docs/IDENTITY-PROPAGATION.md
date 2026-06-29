# Identity Propagation & Delegation Framework

**Version:** 2.0.0 | **Last Updated:** June 2026

User identity, intent, and short-lived delegation tokens propagate through the entire briefing request chain (Gap #18, #118).

## Flow

1. Frontend authenticates the user and sends `user_id` with each briefing request.
2. FastAPI validates the request and initializes `BriefingGraphState` with `user_id`, `request_id`, and `trace_id`.
3. The Orchestrator initializes MCP tool sessions and working memory.
4. Tool agents request delegation via `IdentityManager` (`backend/kernel/identity_manager.py`).
5. MCP clients use scoped credentials; agents never use standing service credentials.

## Delegation Token

```python
DelegationContext(
    user_id="user_12345",
    session_id="sess_abc123",
    agent_id="calendar",
    intent="read_events",
    permissions=("calendar:read",),
    issued_at=...,
    expires_at=...,  # TTL ≤ 15 minutes
    parent_trace_id="...",
)
```

## Components

| Component | Module | Role |
|---|---|---|
| Identity Manager | `backend/kernel/identity_manager.py` | Issues and validates delegation contexts |
| Credential Broker | `backend/security/vault.py` | JIT OAuth tokens scoped to intent |
| Calendar Agent | `backend/agents/calendar/node.py` | Uses `IdentityManager` before MCP calls |

## Confused Deputy Prevention

- Agents act on behalf of users via delegation tokens, not agent-owned credentials.
- Each token is scoped to a single intent (`read_events`, `read_tasks`, `update_tasks`).
- Expired or mismatched tokens raise before any external API call.

See also: `docs/AGENTIC-CONSENT.md`, `docs/SECURITY.md`, `backend/security/delegation.py`.
