# Incident Response Playbook — Parallel Triage

**Gap #130** | **Week 7 (DB-E14)**

Operational runbook for handling multiple concurrent agent security incidents.

---

## Pre-Incident Preparation

- Confirm on-call rotation in `#security-oncall`
- Verify Prometheus dashboards: drift, constitutional violations, dwell time, alert coverage
- Ensure `docs/GOVERNANCE.md` emergency tiers are accessible offline

---

## Parallel Triage Protocol

### Step 1 — Incident Commander (IC) Assignment

First responder becomes IC. IC does **not** execute technical fixes — coordinates only.

```
IC responsibilities:
├── Assign one primary owner per incident
├── Enforce priority matrix (see TABLETOP-EXERCISES.md)
├── Prevent conflicting remediation (track active actions)
└── Declare all-clear per incident
```

### Step 2 — Severity Confirmation (5 min per incident)

| Check | Tool / Doc |
|---|---|
| Is exploitation active? | Audit log tail, `security_violations_total` |
| Blast radius? | `docs/security/MITRE-ATTACK-COVERAGE.md` |
| User impact? | Briefing error rate, consent revocation count |
| Emergency tier? | `docs/GOVERNANCE.md` § Emergency Change Authorization |

### Step 3 — Containment Actions (parallel)

| Incident Type | Immediate Action | Code / Config |
|---|---|---|
| Injection | Block agent input path | Critic + InputSecurityScanner (already wired) |
| Credential leak | Revoke all consent + rotate broker cache | `ConsentStore.revoke()`, broker cache clear |
| Guardrail spike | Circuit-break affected agent | `evaluate_token_budget()`, DLQ route |
| MCP compromise | Stop MCP supervisord programs | `supervisord.conf` — disable calendar/postgres MCP |
| Memory poison | Quarantine layer | `backend/memory/quarantine.py` workflow |

### Step 4 — Communication

- **Internal:** `#incident-daily-briefing` — status every 30 min during P1
- **Users:** Status page if briefing unavailable >15 min
- **Audit:** Log all emergency changes via `AuditLogWriter`

### Step 5 — Recovery Verification

```bash
uv run pytest backend/tests/security/test_jailbreak_corpus.py -v
uv run pytest backend/tests/security/test_hitl_integration.py -v
uv run python -c "from backend.security.mitre_coverage import get_coverage_summary; print(get_coverage_summary())"
```

---

## Anti-Patterns During Multi-Incident

| Anti-Pattern | Why It Fails | Correct Approach |
|---|---|---|
| Single-threaded response | Lower-priority incidents starve | Parallel owners per IC assignment |
| Alert fatigue — mute all | Misses escalation | Mute only correlated sub-alerts |
| Skip audit logging | Breaks forensic chain | Tier 1 still logs with justification |
| Deploy untested hotfix | Cascading failure | Minimal diff + targeted test subset |

---

## Post-Incident

1. Post-incident review within 48h (Tier 1) per `docs/GOVERNANCE.md`
2. Update this playbook with gaps discovered
3. Schedule follow-up red team within 24h (`docs/RED-TEAMING.md`)

---

*Incident Response Playbook — Week 7 Gap Remediation*
