# Week 5 Implementation — Supply Chain Security & JIT Credentials

**Epic:** DB-E12  
**Branch:** `epic/week5-gap-remediation`  
**Status:** planned  
**Started:** 2026-06-06  
**Scope:** Phase 3 gap remediation — AI-BOM, CI supply chain gates, sealed audit logs, JIT credential broker

**Ticket file:** `docs/jira-tickets-json/DB-E12-gap-remediation-week5.json` (DB-E2 `Description` format)  
**Kickoff:** `docs/gaps/WEEK5-KICKOFF-PROMPT.md`  
**Guide:** `docs/gaps/WEEK5-IMPLEMENTATION-GUIDE.md`

### Day 1: AI-BOM (DB-121, Gap #115)
- [ ] Create `infrastructure/ai-bom.yaml`
- [ ] Create `docs/SUPPLY-CHAIN-SECURITY.md`
- [ ] Create `backend/security/bom.py` + `scripts/validate_ai_bom.py`
- [ ] Write tests: `backend/tests/security/test_ai_bom.py`
- [ ] Verify: ruff + mypy + pytest (240+ baseline)

### Day 2: OpenSSF Scorecard & pip-audit (DB-122, Gap #116)
- [ ] Add pip-audit step to `.github/workflows/ci.yml`
- [ ] Ensure `SECURITY.md` at repo root
- [ ] Document Scorecard ≥7.0 threshold in `docs/SUPPLY-CHAIN-SECURITY.md`
- [ ] Write tests: `backend/tests/security/test_supply_chain_ci.py`
- [ ] Verify: ruff + mypy + pytest

### Day 3: Cryptographic Audit Sealing (DB-123, Gaps #123, #51)
- [ ] Create `backend/security/audit.py` (hash chain — distinct from `memory/audit.py`)
- [ ] Alembic migration 006: `audit_log` sealed table
- [ ] Add `audit_log_entries_total` metric
- [ ] Document in `docs/SECURITY.md`
- [ ] Write tests: `backend/tests/security/test_audit_sealing.py`
- [ ] Verify: ruff + mypy + pytest

### Day 4: JIT Credential Broker (DB-124, Gap #19)
- [ ] Create `backend/security/vault.py` (`CredentialBroker`)
- [ ] Wire `backend/mcp/calendar_stdio.py` to broker
- [ ] Add `credential_issuance_total` metric
- [ ] Update `.env.example` with `VAULT_MODE`, `CREDENTIAL_TTL_SECONDS`
- [ ] Write tests: `backend/tests/security/test_vault.py`
- [ ] Verify: ruff + mypy + pytest

### Day 5: Vendor Assessments & Proof (DB-125, Gap #127)
- [ ] Vendor assessment table in `docs/SUPPLY-CHAIN-SECURITY.md`
- [ ] `docs/adr/ADR-supply-chain-week5.md`
- [ ] Integration tests: `backend/tests/security/test_supply_chain_integration.py`
- [ ] Proof package in `proof/week5/`
- [ ] `docs/learning/week5-supply-chain-and-credentials.md`
- [ ] Update `docs/PLAN.md` + `docs/OBSERVABILITY.md`
- [ ] Verify: ruff + mypy + pytest (250+ target)

---

## Verification Gates
- Backend gate: `uv run ruff check backend` → `uv run ruff format backend` → `uv run mypy backend` → `uv run pytest`
- Implement all `EDGE CASES` from each task `Description` in DB-E12 JSON

---

*Last Updated: 2026-06-06*
