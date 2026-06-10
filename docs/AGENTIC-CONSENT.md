# Agentic Consent — AI Daily Briefing Assistant

**Version:** 1.5.0 | **Last Updated:** May 2026

---

## Overview

Agentic Consent is a framework for managing how AI agents access user data and external services. Unlike traditional OAuth flows where users grant permanent access, Agentic Consent uses **time-bounded, transaction-aware authorization** that respects user autonomy.

---

## Core Principles

1. **Ephemeral Access** — Agents receive short-lived tokens, not permanent credentials
2. **Transaction Scope** — Access is granted for specific operations, not blanket permissions
3. **User Visibility** — Users see exactly what agents are accessing and when
4. **Revocable** — Users can revoke consent instantly, mid-operation if needed
5. **Auditable** — All consent grants and usages are logged

---

## Consent Model

### Consent Types

| Type | Duration | Use Case | User Prompt |
|---|---|---|---|
| **Session** | Current session only | One-time data access | "Allow for this briefing" |
| **Time-Bounded** | 1-24 hours | Repeated access pattern | "Allow for 4 hours" |
| **Recurring** | Until revoked | Trusted integrations | "Always allow" |

### Consent Record Schema

```python
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

class ConsentRecord(BaseModel):
    """Record of user consent for agent access."""
    
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    
    # What is being consented to
    service: str  # e.g., "google_calendar"
    scope: list[str]  # e.g., ["calendar.readonly"]
    agent_id: str  # Agent requesting access
    
    # Consent parameters
    consent_type: Literal["session", "time_bounded", "recurring"]
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    
    # Tracking
    times_used: int = 0
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    revocation_reason: str | None = None
    
    @property
    def is_valid(self) -> bool:
        if self.revoked_at:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True
```

---

## Time-Bounded Consent Flow

### Google Calendar Integration

```
┌─────────┐     ┌─────────────┐     ┌────────────────┐     ┌─────────────┐
│  User   │     │  Frontend   │     │    Backend     │     │ Calendar    │
│         │     │             │     │                │     │ MCP         │
└────┬────┘     └──────┬──────┘     └───────┬────────┘     └──────┬──────┘
     │                 │                    │                      │
     │ Request         │                    │                      │
     │ Briefing        │                    │                      │
     │────────────────▶│                    │                      │
     │                 │                    │                      │
     │                 │ POST /briefing     │                      │
     │                 │───────────────────▶│                      │
     │                 │                    │                      │
     │                 │                    │ Check consent        │
     │                 │                    │─────────────────────▶│
     │                 │                    │                      │
     │                 │                    │◀─────────────────────│
     │                 │                    │ consent_required     │
     │                 │                    │                      │
     │                 │◀───────────────────│                      │
     │                 │ Show ConsentModal  │                      │
     │                 │                    │                      │
     │◀────────────────│                    │                      │
     │ "Allow Google   │                    │                      │
     │  Calendar for   │                    │                      │
     │  4 hours?"      │                    │                      │
     │                 │                    │                      │
     │ Click "Allow"   │                    │                      │
     │────────────────▶│                    │                      │
     │                 │                    │                      │
     │                 │ OAuth redirect     │                      │
     │                 │───────────────────▶│                      │
     │                 │                    │                      │
     │                 │                    │ Store consent +      │
     │                 │                    │ tokens (encrypted)   │
     │                 │                    │─────────────────────▶│
     │                 │                    │                      │
     │                 │                    │ Resume briefing      │
     │                 │                    │ generation           │
     │                 │◀───────────────────│                      │
     │◀────────────────│                    │                      │
     │ Briefing ready  │                    │                      │
     │                 │                    │                      │
```

### Default TTL Configuration

OAuth popup URL is auto-built from `GOOGLE_CLIENT_ID` (`GET /api/v1/consent/oauth/google_calendar`). Register redirect URIs in Google Cloud: `http://localhost:8088`, `http://localhost:3010`, and `https://developers.google.com/oauthplayground`. See [guidence/google-calandar-setup.md](./guidence/google-calandar-setup.md).

Calendar API access in production uses `GOOGLE_REFRESH_TOKEN` in `.env`; the popup is optional UX during consent grant.

```python
CONSENT_TTL_HOURS = {
    "google_calendar": 4,  # 4-hour living contract
    "postgres_mcp": 24,    # Internal service, longer TTL
}

def calculate_expiry(service: str, consent_type: str) -> datetime | None:
    if consent_type == "session":
        return None  # Expires with session
    elif consent_type == "time_bounded":
        hours = CONSENT_TTL_HOURS.get(service, 4)
        return datetime.now(timezone.utc) + timedelta(hours=hours)
    elif consent_type == "recurring":
        return None  # No expiry until revoked
```

---

## Human-on-the-Loop Default (Gap #95)

**Week 7 (DB-E14):** Standard briefing runs autonomously with visible override — not full human approval for every step.

| Mode | When | Pipeline Behavior |
|---|---|---|
| **Human-on-the-loop** | Default daily briefing | Agents execute; user sees reasoning trace + observability badge |
| **Human-in-the-loop** | Consensus disagreement, scope-expanding consent | Pipeline pauses at `awaiting_human_review` or consent modal |

Sensitive actions (calendar access, task writes) always require JIT consent regardless of mode.

See `docs/HITL-ARCHITECTURE.md` for the eight-layer model.

---

## Just-In-Time (JIT) Authorization

### Agent Interruption Protocol

When an agent attempts to access an MCP with expired or missing consent:

```python
async def calendar_agent_node(state: BriefingGraphState) -> AgentResultEnvelope:
    """Calendar Agent with JIT consent handling."""
    
    mcp = mcp_manager.get_client("calendar")
    
    try:
        # Attempt MCP call
        result = await mcp.call_tool(
            "get_events",
            {"user_id": state["user_id"], "date": state["requested_at"].date()}
        )
        return AgentResultEnvelope(status="success", result=result, ...)
        
    except MCPConsentRequired as e:
        # Consent expired or never granted
        return AgentResultEnvelope(
            agent_id="calendar",
            status="escalated",
            escalation=EscalationPayload(
                reason="consent_required",
                target_agent="orchestrator",
                context=json.dumps({
                    "service": "google_calendar",
                    "scope": ["calendar.readonly"],
                    "suggested_ttl_hours": 4,
                })
            ),
            metadata=ExecutionMetadata(
                execution_ms=e.elapsed_ms,
                tokens_used=0,
                ...
            ),
        )
```

### Orchestrator Consent Handling

```python
async def orchestrator_handle_consent(
    state: BriefingGraphState,
    escalation: EscalationPayload,
) -> dict:
    """Handle consent escalation from agents."""
    
    context = json.loads(escalation.context)
    
    # Create consent request for frontend
    consent_request = ConsentRequest(
        request_id=state["request_id"],
        service=context["service"],
        scope=context["scope"],
        suggested_ttl_hours=context["suggested_ttl_hours"],
        agent_requesting=escalation.target_agent,
    )
    
    # Pause graph execution and signal frontend
    return {
        "status": "awaiting_consent",
        "consent_request": consent_request.model_dump(),
        "partial_result": state.get("partial_briefing"),
    }
```

---

## Frontend Consent Modal

### ConsentPromptModal Component

```typescript
interface ConsentRequest {
  requestId: string;
  service: 'google_calendar' | 'postgres_mcp';
  scope: string[];
  suggestedTtlHours: number;
  agentRequesting: string;
}

interface ConsentModalProps {
  request: ConsentRequest;
  onGrant: (ttlHours: number) => void;
  onDeny: () => void;
}

function ConsentPromptModal({ request, onGrant, onDeny }: ConsentModalProps) {
  const [selectedTtl, setSelectedTtl] = useState(request.suggestedTtlHours);
  
  const serviceLabels: Record<string, string> = {
    google_calendar: 'Google Calendar',
    postgres_mcp: 'Task Database',
  };
  
  return (
    <Dialog open={true}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Permission Required</DialogTitle>
          <DialogDescription>
            The {request.agentRequesting} agent needs access to your {serviceLabels[request.service]}.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium">Requested permissions:</p>
            <ul className="list-disc list-inside text-sm text-gray-600">
              {request.scope.map((s) => (
                <li key={s}>{formatScope(s)}</li>
              ))}
            </ul>
          </div>
          
          <div>
            <label className="text-sm font-medium">Allow access for:</label>
            <Select value={selectedTtl.toString()} onValueChange={(v) => setSelectedTtl(parseInt(v))}>
              <SelectItem value="0">This briefing only</SelectItem>
              <SelectItem value="1">1 hour</SelectItem>
              <SelectItem value="4">4 hours</SelectItem>
              <SelectItem value="24">24 hours</SelectItem>
            </Select>
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onDeny}>Deny</Button>
          <Button onClick={() => onGrant(selectedTtl)}>Allow</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

---

## Token Lifecycle

### Token Storage

```python
class EncryptedToken(BaseModel):
    """Encrypted OAuth token with metadata."""
    
    user_id: UUID
    service: str
    access_token_encrypted: bytes  # AES-256-GCM encrypted
    refresh_token_encrypted: bytes | None
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Encryption metadata
    encryption_key_id: str  # Key rotation support
    nonce: bytes

class TokenManager:
    """Manages encrypted token storage and refresh."""
    
    async def store_token(
        self,
        user_id: UUID,
        service: str,
        access_token: str,
        refresh_token: str | None,
        expires_in: int,
    ) -> None:
        """Encrypt and store OAuth tokens."""
        encrypted = EncryptedToken(
            user_id=user_id,
            service=service,
            access_token_encrypted=self._encrypt(access_token),
            refresh_token_encrypted=self._encrypt(refresh_token) if refresh_token else None,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            encryption_key_id=self._current_key_id,
            nonce=os.urandom(12),
        )
        await self._db.save(encrypted)
    
    async def get_valid_token(self, user_id: UUID, service: str) -> str | None:
        """Retrieve token, refreshing if needed."""
        token = await self._db.get(user_id, service)
        if not token:
            return None
        
        if token.expires_at < datetime.now(timezone.utc) + timedelta(minutes=5):
            # Token expiring soon, attempt refresh
            if token.refresh_token_encrypted:
                return await self._refresh_token(token)
            return None
        
        return self._decrypt(token.access_token_encrypted)
```

### Token Refresh Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ MCP Client  │────▶│ Token       │────▶│ OAuth       │
│             │     │ Manager     │     │ Provider    │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                           │                    │
                    Check expiry                │
                           │                    │
                    If < 5 min ────────────────▶│
                    remaining        Refresh    │
                           │         request    │
                           │◀───────────────────│
                           │      New tokens    │
                    Encrypt & store             │
                           │                    │
                    Return access token         │
```

---

## Revocation

### User-Initiated Revocation

```http
DELETE /api/v1/consent/{consent_id}
Authorization: Bearer <token>

Response:
{
  "status": "revoked",
  "revoked_at": "2026-05-29T15:00:00Z",
  "service": "google_calendar"
}
```

### Automatic Revocation Triggers

| Trigger | Action |
|---|---|
| Token expiry | Mark consent as expired |
| OAuth error (401) | Revoke consent, prompt re-auth |
| User logout | Revoke session consents |
| Account deletion | Revoke all consents |
| Security violation | Revoke affected consents |

### Revocation Implementation

```python
async def revoke_consent(
    consent_id: UUID,
    reason: str = "user_requested",
) -> None:
    """Revoke consent and invalidate tokens."""
    
    consent = await db.get_consent(consent_id)
    
    # Mark consent as revoked
    consent.revoked_at = datetime.now(timezone.utc)
    consent.revocation_reason = reason
    await db.save(consent)
    
    # Delete associated tokens
    await token_manager.delete_tokens(consent.user_id, consent.service)
    
    # Log for audit
    logger.info(
        "consent_revoked",
        consent_id=str(consent_id),
        user_id=str(consent.user_id),
        service=consent.service,
        reason=reason,
    )
```

---

## Consent Dashboard

Users can view and manage all active consents:

```typescript
interface ConsentDashboardItem {
  id: string;
  service: string;
  scope: string[];
  grantedAt: string;
  expiresAt: string | null;
  timesUsed: number;
  lastUsedAt: string | null;
}

function ConsentDashboard() {
  const { consents } = useConsents();
  
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Active Permissions</h2>
      
      {consents.map((consent) => (
        <Card key={consent.id}>
          <CardHeader>
            <CardTitle>{serviceLabels[consent.service]}</CardTitle>
            <CardDescription>
              Granted {formatDate(consent.grantedAt)}
              {consent.expiresAt && ` · Expires ${formatDate(consent.expiresAt)}`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              Used {consent.timesUsed} times
              {consent.lastUsedAt && ` · Last used ${formatDate(consent.lastUsedAt)}`}
            </p>
          </CardContent>
          <CardFooter>
            <Button variant="destructive" onClick={() => revokeConsent(consent.id)}>
              Revoke Access
            </Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
```

---

## Audit Trail

All consent operations are logged:

```python
class ConsentAuditLog(BaseModel):
    """Audit log for consent operations."""
    
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: UUID
    consent_id: UUID | None
    
    action: Literal[
        "consent_requested",
        "consent_granted",
        "consent_denied",
        "consent_used",
        "consent_expired",
        "consent_revoked",
        "token_refreshed",
    ]
    
    service: str
    agent_id: str | None
    ip_address: str | None
    user_agent: str | None
    
    metadata: dict = Field(default_factory=dict)
```

---

*Agentic Consent Documentation — Version 1.5.0 — May 2026*
