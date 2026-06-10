# Week 5 Implementation Guide — Supply Chain Security & JIT Credentials

**Target:** Phase 3 gap remediation — AI-BOM, CI supply chain gates, sealed audit logs, JIT credentials  
**Duration:** 5 days (40 hours)  
**Epic Ticket:** `docs/jira-tickets-json/DB-E12-gap-remediation-week5.json`  
**Prerequisites:** Week 4 (DB-E11) merged — memory security, live embeddings, Critic v2.0.0, 230+ tests

---

## Implementation Protocol

### Mandatory Reading Order

1. `AGENT.md` — root workflow rules (implement all `EDGE CASES` from task `Description`)
2. `docs/EXECUTION-RULES.md`
3. `docs/tasks/lessons.md` — Week 1–4 learnings
4. `docs/learning/week4-memory-security-and-agentops.md`
5. `007-01-ai-daily-briefing-assistant-v2.0.0.md` — § Supply Chain Security, § JIT Credential Issuance
6. `docs/gaps/WEEK5-KICKOFF-PROMPT.md`
7. `docs/jira-tickets-json/DB-E12-gap-remediation-week5.json` — full task descriptions

### Git Branch Workflow

```bash
git checkout epic/autonomus-implementation-gap
git pull origin epic/autonomus-implementation-gap
git checkout -b epic/week5-gap-remediation
git push -u origin epic/week5-gap-remediation
```

### JSON Ticket Format

Week 5 tasks use the **DB-E2 Description pattern** — each task `Description` includes:

- `IMPLEMENTATION DETAILS`
- `EFFORT`
- `PROJECT AREA`
- `DEPENDENCIES`
- `TESTING CRITERIA`
- `EDGE CASES`

Coding agents must implement every edge case before marking a task done.

**Backend verification gate (every day, before marking tasks done):**

```bash
uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest
```

---

## Day 1: AI-BOM (DB-121, Gap #115)

### Goals

- Track provenance of models, embeddings, and critical Python libraries
- Automate manifest validation against runtime settings

### Key Files

| File | Change |
|---|---|
| `infrastructure/ai-bom.yaml` | Models, embeddings, libraries manifest |
| `docs/SUPPLY-CHAIN-SECURITY.md` | AI-BOM policy and update cadence |
| `backend/security/bom.py` | `load_ai_bom()`, `validate_bom_freshness()` |
| `scripts/validate_ai_bom.py` | CLI validator for CI |

### ai-bom.yaml Structure (minimum)

```yaml
metadata:
  version: "1.0"
  last_updated: "2026-06-06"
  owner: "platform-security"
models:
  - name: openai/gpt-4o-mini
    provider: openrouter
    license: Commercial
embeddings:
  - name: openai/text-embedding-3-small
    provider: openrouter
    dimensions: 1536
libraries:
  - name: langgraph
    version: "0.4.x"
    license: MIT
```

---

## Day 2: OpenSSF Scorecard & pip-audit (DB-122, Gap #116)

### Goals

- Block CI on critical dependency CVEs
- Document OpenSSF Scorecard thresholds and manual run procedure

### Key Files

| File | Change |
|---|---|
| `.github/workflows/ci.yml` | Add pip-audit step to backend job |
| `SECURITY.md` | Create at repo root if missing |
| `docs/SUPPLY-CHAIN-SECURITY.md` | Scorecard § with ≥7.0 threshold |

### CI Addition (pattern)

```yaml
- name: pip-audit
  run: uv run pip-audit --desc on
```

---

## Day 3: Cryptographic Audit Sealing (DB-123, Gaps #123, #51)

### Goals

- Append-only audit log with SHA-256 hash chain
- Tamper detection via `verify_audit_chain()`

### Key Files

| File | Change |
|---|---|
| `backend/security/audit.py` | `AuditLogWriter`, `verify_audit_chain()` |
| `alembic/versions/006_audit_log_sealed.py` | `audit_log` table |
| `backend/observability/metrics.py` | `audit_log_entries_total`, `audit_chain_verification_failures_total` |
| `docs/SECURITY.md` | § Cryptographic Audit Integrity |

### Hash Chain

```
entry_hash = sha256(prev_hash + canonical_json(entry_without_hash))
genesis_prev_hash = "0" * 64
```

**Note:** `backend/memory/audit.py` tracks memory reads — do not merge with `backend/security/audit.py`.

---

## Day 4: JIT Credential Broker (DB-124, Gap #19)

### Goals

- Issue short-lived credentials on demand for MCP tool calls
- Audit every issuance; never pass raw refresh tokens to MCP env

### Key Files

| File | Change |
|---|---|
| `backend/security/vault.py` | `CredentialBroker`, `Credential` models |
| `backend/mcp/calendar_stdio.py` | Use broker for access token |
| `backend/settings.py` | `vault_mode`, `credential_ttl_seconds` |
| `.env.example` | `VAULT_MODE`, `CREDENTIAL_TTL_SECONDS` |

### Broker Interface

```python
credential = await broker.get_credential(
    user_id=user_id,
    service="google_calendar",
    intent="read_events",
    ttl_seconds=900,
)
```

---

## Day 5: Vendor Assessments & Proof (DB-125, Gap #127)

### Goals

- Document SaaS and FOSS vendor security posture
- Integration tests across BOM + audit + broker
- Proof package and learning doc

### Deliverables

- `docs/adr/ADR-supply-chain-week5.md`
- `backend/tests/security/test_supply_chain_integration.py`
- `proof/week5/` — test output, BOM snapshot
- `docs/learning/week5-supply-chain-and-credentials.md`

---

## Success Criteria

| Metric | Target |
|---|---|
| AI-BOM validation | CI step passes on every PR |
| pip-audit | Zero critical CVEs in production deps |
| Audit chain | Tamper detection 100% in test corpus |
| Credential TTL | All issued tokens expire ≤900s |
| Test count | 240+ passing (+10 from Week 4 baseline) |

---

*Week 5 Implementation Guide — Created 2026-06-06*
