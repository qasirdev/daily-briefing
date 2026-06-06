# Week 6 Implementation — OWASP Agent Top 10 & Advanced Defenses

**Epic:** DB-E13  
**Branch:** `epic/week6-gap-remediation`  
**Status:** complete  
**Started:** 2026-06-06  
**Scope:** Phase 4 gap remediation — OWASP Agent Top 10, constitutional classifiers, MITRE ATT&CK, drift/dwell SLOs

**Ticket file:** `docs/jira-tickets-json/DB-E13-gap-remediation-week6.json`  
**Kickoff:** `docs/gaps/WEEK6-KICKOFF-PROMPT.md`  
**Guide:** `docs/gaps/WEEK6-IMPLEMENTATION-GUIDE.md`

### Day 1: OWASP Agent Top 10 (DB-126, Gaps #62-65)
- [x] Create `backend/security/owasp_agent.py`
- [x] Add OWASP Agent matrix to `docs/SECURITY.md`
- [x] Write tests: `backend/tests/security/test_owasp_agent_top10.py`
- [x] Verify: ruff + mypy + pytest

### Day 2: Constitutional Classifiers (DB-127, Gap #126)
- [x] Create `backend/security/rules.yaml`
- [x] Create `constitutional_classifier.py` + `input_scanner.py`
- [x] Wire Critic agent to `InputSecurityScanner`
- [x] Jailbreak corpus + tests (≥95% block rate)
- [x] Verify: ruff + mypy + pytest

### Day 3: MITRE ATT&CK (DB-128, Gap #129)
- [x] Create `docs/security/MITRE-ATTACK-COVERAGE.md`
- [x] Create `backend/security/mitre_coverage.py`
- [x] Write tests: `backend/tests/security/test_mitre_coverage.py`
- [x] Coverage ratio 92.86% (≥80% target)
- [x] Verify: ruff + mypy + pytest

### Day 4: Drift, Dwell Time, Alerts (DB-129, Gaps #122, #134, #135)
- [x] Create `backend/observability/drift_monitor.py`
- [x] Add metrics: dwell time, alert coverage, long-term drift
- [x] Write tests: `backend/tests/observability/test_dwell_time_and_alerts.py`
- [x] Verify: ruff + mypy + pytest

### Day 5: Red Teaming & Consent (DB-130, Gaps #88, #98)
- [x] Create `docs/RED-TEAMING.md`
- [x] Add `action_payload` to consent flow (backend + frontend)
- [x] Integration tests: `test_governance_integration.py`
- [x] Proof package in `proof/week6/`
- [x] `docs/learning/week6-owasp-agent-governance.md`
- [x] Updated `docs/PLAN.md`
- [x] Verify: 361 passed, 3 skipped

---

## Verification Gates
- Backend gate (required before marking any day/task done):
  ```bash
  uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest
  ```
- Jailbreak corpus: `uv run pytest backend/tests/security/test_jailbreak_corpus.py -v`
- MITRE summary: `uv run python -c "from backend.security.mitre_coverage import get_coverage_summary; print(get_coverage_summary())"`

---

*Last Updated: 2026-06-06*
