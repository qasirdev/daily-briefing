# KICKOFF PROMPT — Week 5: Supply Chain Security & JIT Credentials

**Epic:** DB-E12 — Week 5 Gap Remediation  
**Integration Branch:** `epic/autonomus-implementation-gap`  
**Feature Branch:** `epic/week5-gap-remediation`  
**Duration:** 5 days (40 hours)

**Scope:** Phase 3 — AI-BOM, OpenSSF Scorecard CI, cryptographic audit sealing, JIT credential broker, vendor assessments

---

## Mission

Establish supply chain security controls (AI-BOM, dependency auditing, vendor registry), implement tamper-evident audit logging, and deliver a JIT credential broker so MCP clients never hold long-lived tokens in process memory.

**Epic Ticket:** `docs/jira-tickets-json/DB-E12-gap-remediation-week5.json`  
**Tasks:** DB-121 (Day 1) through DB-125 (Day 5)

**Primary Deliverables:**
1. AI-BOM manifest + `docs/SUPPLY-CHAIN-SECURITY.md` (DB-121, Gap #115)
2. pip-audit + OpenSSF Scorecard policy in CI (DB-122, Gap #116)
3. Hash-chained audit log sealing (DB-123, Gaps #123, #51)
4. JIT CredentialBroker wired to Calendar MCP (DB-124, Gap #19)
5. Vendor/FOSS assessments + proof package (DB-125, Gap #127)

---

## Mandatory Reading (Before Implementation)

1. `AGENT.md` — review `Description` field rule in workflow table
2. `docs/EXECUTION-RULES.md`
3. `docs/tasks/lessons.md` — Week 1–4 learnings
4. `docs/learning/week4-memory-security-and-agentops.md`
5. `007-01-ai-daily-briefing-assistant-v2.0.0.md` — § Supply Chain Security, § JIT Credential Issuance, § Observability
6. `docs/gaps/WEEK5-IMPLEMENTATION-GUIDE.md`
7. `docs/jira-tickets-json/DB-E12-gap-remediation-week5.json` — read each task `Description` for edge cases
8. `backend/AGENT.md`

---

## Pre-Implementation Checklist

```bash
git checkout epic/autonomus-implementation-gap
git pull origin epic/autonomus-implementation-gap
git checkout -b epic/week5-gap-remediation
git push -u origin epic/week5-gap-remediation

uv sync
uv run pytest -v   # Week 4 baseline must pass (230+)

# Verify Week 4 metrics still exposed
curl http://localhost:8010/metrics | grep -E 'embedding_|memory_quarantine|consensus_disagreement'
```

Write plan to `docs/tasks/todo.md` before touching code.

---

## Daily Workflow

| Day | Task | Focus |
|---|---|---|
| 1 | DB-121 | AI-BOM manifest + supply chain docs |
| 2 | DB-122 | pip-audit + OpenSSF Scorecard CI gates |
| 3 | DB-123 | Cryptographic audit log hash chain |
| 4 | DB-124 | JIT CredentialBroker + MCP integration |
| 5 | DB-125 | Vendor assessments, integration tests, proof |

**Per-day gate:** `uv run ruff check backend` → `uv run ruff format backend` → `uv run mypy backend` → `uv run pytest`

**Edge cases:** Implement every `EDGE CASES` block from the task `Description` in `DB-E12-gap-remediation-week5.json`.

---

## Success Criteria

**AI-BOM (Day 1):**
- `infrastructure/ai-bom.yaml` lists all LLM, embedding, and critical library components
- `scripts/validate_ai_bom.py` passes in CI

**Supply Chain CI (Day 2):**
- pip-audit blocks critical CVEs
- `docs/SUPPLY-CHAIN-SECURITY.md` documents Scorecard ≥7.0 threshold

**Audit Sealing (Day 3):**
- `verify_audit_chain()` detects tampered entries
- Delegation and consent events append to sealed log

**Credential Broker (Day 4):**
- Credentials expire within 900s TTL
- Calendar MCP uses broker; `credential_issuance_total` metric exposed

**Day 5:**
- Vendor assessment table complete for SaaS + FOSS dependencies
- `proof/week5/` complete
- `docs/learning/week5-supply-chain-and-credentials.md` written
- 240+ tests passing

---

## Week 6 Preview

- OWASP Agent Top 10 compliance + red teaming — DB-E13
- Constitutional classifiers (Gap #126)
- MITRE ATT&CK detection mapping (Gap #129)

---

*Week 5 Kickoff — Created 2026-06-06*
