# Security & OWASP GenAI Hardening — AI Daily Briefing Assistant

**Version:** 1.5.0 | **Last Updated:** May 2026

---

## Security Principles

1. **Zero-Trust Input** — All external data is untrusted until validated
2. **Defense in Depth** — Multiple security layers, no single point of failure
3. **Least Privilege** — Agents have minimal required permissions
4. **Fail Secure** — Security failures result in denial, not bypass
5. **Audit Everything** — All security events are logged and traceable

---

## OWASP GenAI Top 10 Compliance Matrix

| ID | Vulnerability | Status | Mitigation | Test Coverage |
|---|---|---|---|---|
| **LLM01** | Prompt Injection | ⬜ Specified | Critic Agent scanning, input sanitization | `tests/security/test_injection.py` |
| **LLM02** | Insecure Output Handling | ⬜ Specified | DOMPurify (FE), nh3 (BE), Orchestrator-as-Presenter | `tests/security/test_sanitization.py` |
| **LLM03** | Training Data Poisoning | ⬜ N/A | No custom model training | N/A |
| **LLM04** | Model Denial of Service | ⬜ Specified | Token budgets, circuit breakers, rate limiting | `tests/security/test_rate_limits.py` |
| **LLM05** | Supply Chain Vulnerabilities | ⬜ Specified | Dependency scanning, lockfile pinning | `tests/security/test_dependencies.py` |
| **LLM06** | Sensitive Information Disclosure | ⬜ Specified | PII masking, data classification | `tests/security/test_pii_masking.py` |
| **LLM07** | Insecure Plugin Design | ⬜ Specified | MCP allowlists, SSRF defense | `tests/security/test_mcp_security.py` |
| **LLM08** | Excessive Agency | ⬜ Specified | Read-only scopes, explicit tool boundaries | `tests/security/test_agent_scope.py` |
| **LLM09** | Overreliance | ⬜ N/A | UX guidance (out of scope) | N/A |
| **LLM10** | Model Theft | ⬜ N/A | No proprietary models | N/A |

---

## Prompt Injection Defense

### Threat Model

Calendar events created by third parties (meeting invites) are prime vectors for **Indirect Prompt Injection**. A malicious actor can craft an event description that attempts to override LLM instructions.

### Detection Pipeline

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Calendar MCP    │────▶│ Critic Agent    │────▶│ Focus Agent     │
│ fetches raw     │     │ scans for       │     │ (safe input)    │
│ event data      │     │ injection       │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  If flagged:    │
                        │  - Scrub payload│
                        │  - Log security │
                        │  - Route to DLQ │
                        └─────────────────┘
```

### Detection Patterns

The Critic Agent uses pattern matching to identify injection attempts:

```python
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions?",
    r"disregard\s+(your\s+)?(training|instructions?)",
    r"you\s+are\s+now\s+(in\s+)?debug\s+mode",
    r"\[\[SYSTEM\]\]",
    r"<\|im_start\|>",
    r"```system",
    r"as\s+an?\s+AI,?\s+you\s+(must|should|will)",
    r"override\s+(all\s+)?safety",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"jailbreak",
]
```

### Escalation Protocol

When injection is detected:

1. **Quarantine** — Payload is immediately quarantined
2. **Log** — Security event logged with full context and trace_id
3. **Escalate** — `AgentResultEnvelope.escalation.reason = "security_violation_detected"`
4. **No Retry** — Security violations are NEVER retried
5. **DLQ** — Event persisted for security team review

```json
{
  "agent_id": "critic",
  "status": "escalated",
  "escalation": {
    "reason": "security_violation_detected",
    "target_agent": "orchestrator",
    "context": "Indirect prompt injection in calendar event 'Team Sync': pattern matched 'ignore previous instructions'"
  }
}
```

---

## Output Sanitization (LLM02)

### Orchestrator-as-Presenter Pattern

Only the Orchestrator produces user-facing content. All other agents return **strict JSON**:

| Agent | Output Format | UI Rendering |
|---|---|---|
| Task Agent | JSON (task list) | ❌ Never directly |
| Calendar Agent | JSON (events) | ❌ Never directly |
| Focus Agent | JSON (plan) | ❌ Never directly |
| Critic Agent | JSON (review) | ❌ Never directly |
| **Orchestrator** | Sanitized Markdown | ✅ After sanitization |

### Backend Sanitization (Python)

```python
import nh3
from markdown import markdown

ALLOWED_TAGS = {
    "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "strong", "em", "code", "pre",
    "blockquote", "hr", "br", "a"
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"}
}

def sanitize_markdown(raw_md: str) -> str:
    """Convert markdown to HTML and strip dangerous content."""
    html = markdown(raw_md, extensions=["fenced_code"])
    return nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
```

### Frontend Sanitization (TypeScript)

```typescript
import DOMPurify from 'dompurify';

const DOMPURIFY_CONFIG = {
  ALLOWED_TAGS: ['p', 'h1', 'h2', 'h3', 'ul', 'ol', 'li', 'strong', 'em', 'code', 'pre', 'a'],
  ALLOWED_ATTR: ['href', 'title'],
  KEEP_CONTENT: true,
};

export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, DOMPURIFY_CONFIG);
}
```

---

## Denial of Wallet Protection (LLM04)

### Token Budget Enforcement

Each agent has explicit token budgets:

| Agent | Input Budget | Output Budget | Hard Limit |
|---|---|---|---|
| Task Agent | 2,000 | 1,000 | 2x |
| Calendar Agent | 2,000 | 1,000 | 2x |
| Focus Agent | 4,000 | 2,000 | 2x |
| Critic Agent | 4,000 | 1,000 | 2x |
| **Total Request** | 12,000 | 5,000 | — |

### Circuit Breaker Implementation

```python
class TokenBudgetExceeded(Exception):
    """Raised when agent exceeds 2x token budget."""
    pass

async def enforce_token_budget(
    agent_id: str,
    tokens_used: int,
    budget: int
) -> None:
    if tokens_used > budget * 2:
        raise TokenBudgetExceeded(
            f"Agent {agent_id} exceeded 2x budget: {tokens_used}/{budget}"
        )
```

### Rate Limiting

| Endpoint | Rate Limit | Window |
|---|---|---|
| `/api/v1/briefing/generate` | 10 requests | 1 minute |
| `/api/v1/tasks/*` | 60 requests | 1 minute |
| `/api/v1/export` | 5 requests | 1 hour |

---

## MCP Security (LLM07)

### PostgreSQL MCP

| Control | Implementation |
|---|---|
| **Access Scope** | Read-only for Task Agent |
| **Row Level Security** | `user_id` filter on all queries |
| **Query Validation** | Parameterized queries only |
| **Connection** | Local TCP, no external exposure |

### Google Calendar MCP

| Control | Implementation |
|---|---|
| **SSRF Defense** | Outbound restricted to `*.googleapis.com` |
| **Token Scope** | `calendar.readonly` only |
| **Consent** | JIT authorization, 4-hour TTL |
| **Input Sanitization** | All event data scanned for injection |

---

## Agent Scope Boundaries (LLM08)

| Agent | Permitted Actions | Prohibited Actions |
|---|---|---|
| Task Agent | Read tasks, Read preferences | Write, Delete, External API |
| Calendar Agent | Read calendar | Write, Delete, Non-Google API |
| Focus Agent | Generate text | Any tool/MCP access |
| Critic Agent | Evaluate text, Security scan | Any tool/MCP access |
| Orchestrator | Coordinate, Present | Direct external API calls |

---

## Data Classification

All data is classified for handling:

| Classification | Description | Handling |
|---|---|---|
| `public` | Non-sensitive metadata | Standard logging |
| `internal` | System operational data | Masked in external logs |
| `confidential` | Business sensitive | Encrypted at rest |
| `confidential_pii` | Personal identifiable info | Encrypted, masked, minimal retention |

### PII Handling

```python
class ExecutionMetadata(BaseModel):
    data_classification: Literal["public", "internal", "confidential", "confidential_pii"]
    
    @model_validator(mode="after")
    def enforce_pii_handling(self) -> "ExecutionMetadata":
        if self.data_classification == "confidential_pii":
            # TODO: DB-112 Implement strict masking and local LLM routing
            pass
        return self
```

---

## Cryptographic Standards

| Use Case | Algorithm | Key Size |
|---|---|---|
| JWT Signing | RS256 | 2048-bit RSA |
| Password Hashing | Argon2id | Default params |
| At-Rest Encryption | AES-256-GCM | 256-bit |
| TLS | TLS 1.3 | — |

---

## Authentication & Authorization

### OAuth 2.0 Flow (Google Calendar)

```
┌────────┐     ┌─────────────┐     ┌────────────────┐
│ User   │────▶│ Frontend    │────▶│ Google OAuth   │
└────────┘     └─────────────┘     └────────┬───────┘
                                            │
                                   ┌────────▼───────┐
                                   │ Consent Modal  │
                                   │ (JIT, 4hr TTL) │
                                   └────────┬───────┘
                                            │
┌────────────────┐     ┌────────────────────▼───────┐
│ Calendar MCP   │◄────│ Token Exchange (Backend)   │
└────────────────┘     └────────────────────────────┘
```

### Session Management

- Sessions use HTTP-only, Secure, SameSite=Strict cookies
- Session tokens rotated on privilege escalation
- Absolute timeout: 24 hours
- Idle timeout: 4 hours

---

## Security Event Logging

All security events are logged with structured fields:

```python
import structlog

security_logger = structlog.get_logger("security")

security_logger.warning(
    "prompt_injection_detected",
    trace_id=state.trace_id,
    user_id=state.user_id,
    agent_id="critic",
    event_id=calendar_event.id,
    pattern_matched="ignore previous instructions",
    action_taken="quarantine_and_dlq",
)
```

---

## Incident Response

### Security Event Severity Levels

| Level | Description | Response Time |
|---|---|---|
| **P1 Critical** | Active exploitation, data breach | Immediate |
| **P2 High** | Vulnerability with exploit potential | 4 hours |
| **P3 Medium** | Security misconfiguration | 24 hours |
| **P4 Low** | Minor security improvement | Next sprint |

### Response Checklist

- [ ] Identify and contain the incident
- [ ] Preserve evidence (logs, DLQ entries)
- [ ] Assess impact and scope
- [ ] Remediate vulnerability
- [ ] Notify affected users if required
- [ ] Post-incident review

---

*Security Documentation — Version 1.5.0 — May 2026*
