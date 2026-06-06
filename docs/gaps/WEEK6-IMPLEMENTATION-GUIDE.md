# Week 6 Implementation Guide — OWASP Agent Top 10 & Advanced Defenses

**Target:** Phase 4 gap remediation — OWASP Agent Top 10, constitutional classifiers, MITRE ATT&CK, drift/dwell SLOs  
**Duration:** 5 days (40 hours)  
**Epic Ticket:** `docs/jira-tickets-json/DB-E13-gap-remediation-week6.json`  
**Prerequisites:** Week 5 (DB-E12) complete — supply chain, audit sealing, JIT credentials, 298+ tests

---

## Day 1: OWASP Agent Top 10 (DB-126)

| File | Purpose |
|---|---|
| `backend/security/owasp_agent.py` | AGENT01–AGENT10 control registry |
| `docs/SECURITY.md` | Compliance matrix section |
| `backend/tests/security/test_owasp_agent_top10.py` | Per-control test reference validation |

---

## Day 2: Constitutional Classifiers (DB-127)

| File | Purpose |
|---|---|
| `backend/security/rules.yaml` | Constitutional rules |
| `backend/security/constitutional_classifier.py` | Rule-based classifier |
| `backend/security/input_scanner.py` | Regex + constitutional unified scan |
| `backend/tests/security/jailbreak_corpus.yaml` | ≥95% block rate corpus |

Wire Critic agent via `InputSecurityScanner`.

---

## Day 3: MITRE ATT&CK (DB-128)

| File | Purpose |
|---|---|
| `docs/security/MITRE-ATTACK-COVERAGE.md` | 22-technique mapping |
| `backend/security/mitre_coverage.py` | Registry + `get_coverage_summary()` |
| `backend/tests/security/test_mitre_coverage.py` | Coverage ratio ≥0.80 |

---

## Day 4: Drift, Dwell Time, Alert Coverage (DB-129)

| File | Purpose |
|---|---|
| `backend/observability/drift_monitor.py` | Long-term drift + alert tracking |
| `backend/observability/metrics.py` | New histograms/gauges |
| `backend/tests/observability/test_dwell_time_and_alerts.py` | SLO tests |

Metrics: `security_dwell_time_seconds`, `security_alert_investigation_coverage`, `long_term_drift_ratio`

---

## Day 5: Red Teaming & Consent Hardening (DB-130)

| File | Purpose |
|---|---|
| `docs/RED-TEAMING.md` | Cadence tied to drift alerts |
| `ConsentPromptRequest.action_payload` | OWASP Agent #9 defense |
| `frontend/components/ConsentPromptModal.tsx` | Machine-readable payload display |
| `proof/week6/` | Proof package |

---

## Success Criteria

| Metric | Target |
|---|---|
| OWASP Agent controls | 10/10 documented |
| Jailbreak block rate | ≥95% |
| MITRE coverage ratio | ≥80% |
| Dwell time SLO | P95 <3600s documented |
| Alert investigation | >95% target documented |
| Tests | 310+ passing |

---

## Backend Verification Gate

Before marking any day or task complete:

```bash
uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest
```

---

*Week 6 Implementation Guide — Created 2026-06-06*
