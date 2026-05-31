# Data Ownership & Privacy — AI Daily Briefing Assistant

**Version:** 1.6.0 (Option 1 Enterprise Hybrid) | **Last Updated:** May 2026

---

## Core Principles

1. **User Ownership** — Users own their data; we are custodians
2. **Minimal Collection** — Collect only what's necessary for the service
3. **Transparent Processing** — Users understand how their data is used
4. **Portability** — Users can export all their data at any time
5. **Right to Deletion** — Users can delete their data completely

---

## Data Classification

All data in the system is classified according to sensitivity:

| Classification | Description | Examples | Retention | Access |
|---|---|---|---|---|
| `public` | Non-sensitive metadata | App version, feature flags | Indefinite | All services |
| `internal` | Operational data | Execution metrics, error counts | 90 days | Backend services |
| `confidential` | Business sensitive | Task titles, preferences | User-controlled | Authenticated only |
| `confidential_pii` | Personal identifiable | Calendar events, user email | Minimal | Strict access control |

### Data Flow Classification

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Classification Flow                 │
│                                                              │
│  User Input ──▶ [confidential_pii] ──▶ Calendar MCP        │
│                                        │                     │
│                                        ▼                     │
│                              ┌─────────────────┐             │
│                              │ Critic Agent    │             │
│                              │ (screens PII)   │             │
│                              └────────┬────────┘             │
│                                       │                      │
│                    ┌──────────────────┼──────────────────┐   │
│                    ▼                  ▼                  ▼   │
│             [confidential]     [internal]          [public]  │
│             Focus Agent        Metrics             Logs      │
│             (no raw PII)       (aggregated)        (masked)  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## GDPR Compliance

### Lawful Basis for Processing

| Data Category | Lawful Basis | Justification |
|---|---|---|
| Account information | Contract | Required for service provision |
| Calendar data | Consent | Explicit opt-in via OAuth |
| Task data | Contract | Core service functionality |
| Usage analytics | Legitimate interest | Service improvement |
| Security logs | Legal obligation | Security incident investigation |

### Data Subject Rights Implementation

| Right | Implementation | Endpoint |
|---|---|---|
| **Access** | Full data export | `GET /api/v1/export` |
| **Rectification** | Edit via UI/API | Standard CRUD endpoints |
| **Erasure** | Account deletion | `DELETE /api/v1/account` |
| **Portability** | JSON/CSV export | `GET /api/v1/export?format=json` |
| **Restriction** | Pause processing | `POST /api/v1/account/pause` |
| **Objection** | Opt-out mechanisms | Settings UI |

### Data Processing Records

```python
class DataProcessingRecord(BaseModel):
    """Record of data processing activity for GDPR compliance."""
    
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    activity_type: Literal[
        "collection",
        "processing",
        "storage",
        "transfer",
        "deletion",
        "export",
    ]
    data_categories: list[str]
    purpose: str
    lawful_basis: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    retention_period_days: int
    recipient: str | None = None  # For transfers
```

---

## Data Portability

### Export Endpoint

```http
GET /api/v1/export
Authorization: Bearer <token>
Accept: application/json

Response:
{
  "export_id": "exp_123",
  "created_at": "2026-05-29T10:00:00Z",
  "format": "json",
  "data": {
    "user": {
      "id": "usr_abc123",
      "email": "user@example.com",
      "created_at": "2026-01-15T08:00:00Z"
    },
    "preferences": {
      "preferred_work_start": "09:00",
      "preferred_deep_work_duration": 120,
      "focus_preferences": ["morning deep work", "afternoon meetings"]
    },
    "tasks": [
      {
        "id": "tsk_001",
        "title": "Review quarterly report",
        "priority": "high",
        "due_date": "2026-05-30",
        "status": "pending",
        "created_at": "2026-05-25T14:00:00Z"
      }
    ],
    "briefing_history": [
      {
        "id": "brf_001",
        "generated_at": "2026-05-29T07:00:00Z",
        "status": "success",
        "content": "Your daily briefing..."
      }
    ],
    "dlq_events": [],
    "consent_records": [
      {
        "service": "google_calendar",
        "granted_at": "2026-05-01T10:00:00Z",
        "scope": "calendar.readonly",
        "expires_at": "2026-05-01T14:00:00Z"
      }
    ]
  }
}
```

### Export Format Options

| Format | Content-Type | Use Case |
|---|---|---|
| JSON | `application/json` | Machine-readable, full fidelity |
| CSV | `text/csv` | Spreadsheet import |
| ZIP | `application/zip` | Large exports with attachments |

### Rate Limits

- Maximum 5 export requests per hour
- Export generation may be asynchronous for large datasets
- Users notified via email when export is ready

---

## Data Retention Policies

### Retention Schedule

| Data Type | Retention Period | Deletion Method |
|---|---|---|
| Active tasks | User-controlled | Manual or completed |
| Completed tasks | 365 days | Automatic purge |
| Briefing history | 90 days | Automatic purge |
| DLQ events | 30 days | Automatic purge |
| Security logs | 2 years | Automatic purge |
| Consent records | Duration + 7 years | Legal requirement |
| Account data | Until deletion request | Manual via request |

### Automatic Purge Implementation

```python
from datetime import datetime, timedelta, timezone

async def purge_expired_data(pool):
    """Daily job to purge data past retention period using asyncpg."""
    
    now = datetime.now(timezone.utc)
    
    async with pool.acquire() as conn:
        # Briefing history (90 days)
        await conn.execute(
            "DELETE FROM briefing_history WHERE created_at < $1",
            now - timedelta(days=90)
        )
        
        # DLQ events (30 days)
        await conn.execute(
            "DELETE FROM dlq_events WHERE created_at < $1",
            now - timedelta(days=30)
        )
        
        # Completed tasks (365 days)
        await conn.execute(
            "DELETE FROM tasks WHERE status = 'completed' AND completed_at < $1",
            now - timedelta(days=365)
        )
    
    logger.info("data_purge_completed", purged_at=now)
```

---

## Learner Feedback Loops

### Preference Learning

The Orchestrator learns from user behavior to improve briefing quality:

```
┌────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ User edits     │────▶│ Orchestrator    │────▶│ Preference      │
│ briefing in UI │     │ analyzes delta  │     │ stored          │
└────────────────┘     └─────────────────┘     └─────────────────┘
                                                       │
                                                       ▼
                                               ┌─────────────────┐
                                               │ Focus Agent     │
                                               │ uses preference │
                                               │ in next run     │
                                               └─────────────────┘
```

### Preference Extraction

```python
class UserPreference(BaseModel):
    """Learned user preference."""
    
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    preference_type: Literal[
        "time_preference",
        "task_priority",
        "meeting_buffer",
        "focus_duration",
        "tone_preference",
    ]
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    learned_from: UUID  # Reference to briefing that triggered learning
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "preference_type": "time_preference",
                "value": "User prefers deep work in the morning (before 11am)",
                "confidence": 0.85
            }
        }
    )
```

### Privacy Safeguards for Learning

| Safeguard | Implementation |
|---|---|
| **Opt-out** | Users can disable preference learning |
| **Transparency** | Users can view all learned preferences |
| **Deletion** | Preferences deleted with account |
| **No external sharing** | Preferences never sent to third parties |
| **Local processing** | Learning happens on-device when possible |

---

## PII Handling

### PII Detection

```python
import re

PII_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "phone": r"\+?[\d\s\-\(\)]{10,}",
    "ssn": r"\d{3}-\d{2}-\d{4}",
    "credit_card": r"\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}",
}

def detect_pii(text: str) -> list[str]:
    """Detect PII patterns in text."""
    detected = []
    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, text):
            detected.append(pii_type)
    return detected
```

### PII Masking for Logs

```python
def mask_pii(text: str) -> str:
    """Mask PII before logging."""
    masked = text
    masked = re.sub(PII_PATTERNS["email"], "[EMAIL]", masked)
    masked = re.sub(PII_PATTERNS["phone"], "[PHONE]", masked)
    # ... other patterns
    return masked
```

### Data Classification Enforcement

```python
class ExecutionMetadata(BaseModel):
    data_classification: Literal["public", "internal", "confidential", "confidential_pii"]
    
    @model_validator(mode="after")
    def enforce_pii_handling(self) -> "ExecutionMetadata":
        if self.data_classification == "confidential_pii":
            # Enforced in backend/llm/router.py: local LLM if enabled,
            # else mask_pii() before OpenRouter. See docs/LOCAL-LLM.md.
            pass
        return self
```

---

## Persistence (Option 1 — Supabase)

| Store | Technology | Tables / data |
|---|---|---|
| **Supabase PostgreSQL** (:6543 Supavisor) | SQLAlchemy async + Alembic | `tasks`, `dlq_events`, `user_preferences`, `consent_records`, `consent_audit_log` |
| **Task reads (agents)** | PostgreSQL MCP stdio only | Agents do not write SQL directly |
| **Calendar reads (agents)** | Calendar MCP stdio | Events not persisted; fetched per briefing |

Connection strings: `DATABASE_URL` (asyncpg) and `MCP_POSTGRES_URL` (sync, for MCP). See [guidence/supabase-setup.md](./guidence/supabase-setup.md).

---

## Third-Party Data Sharing

### Data Shared with LLM Providers

| Provider | Data Shared | Safeguards |
|---|---|---|
| OpenRouter | Task titles, calendar summaries (masked) | `mask_pii()` before outbound calls when `confidential_pii` |
| Local LLM | Full context when enabled | No third-party transmission; Docker: use `host.docker.internal` |

### Data NOT Shared

- Raw calendar event descriptions (injection risk)
- User email addresses
- Account credentials
- Full briefing history
- Learned preferences

### OpenRouter Privacy Agreement

```python
LLM_REQUEST_SANITIZATION = {
    "strip_emails": True,
    "strip_phone_numbers": True,
    "anonymize_names": True,
    "max_context_tokens": 4000,
}
```

---

## Audit Trail

All data access is logged for compliance:

```python
class DataAccessLog(BaseModel):
    """Audit log for data access."""
    
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: UUID
    accessor_id: str  # Agent or service that accessed data
    access_type: Literal["read", "write", "delete", "export"]
    data_type: str
    data_classification: str
    success: bool
    ip_address: str | None = None
```

---

*Data Ownership Documentation — Version 1.5.0 — May 2026*
