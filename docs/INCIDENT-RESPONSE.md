# Incident Response — AI Daily Briefing Assistant

**Gap #131** | **Week 7 (DB-E14)**

Procedures for detecting, triaging, and resolving agent security incidents.

---

## Severity Classification

| Severity | Examples | Response SLA | Escalation Tier |
|---|---|---|---|
| **P1 Critical** | Active injection exploit, credential leak, rogue drift ≥2× | 15 min acknowledge, 1 hr contain | Tier 1 |
| **P2 High** | Guardrail spike, MITRE blind spot triggered, consent bypass attempt | 1 hr acknowledge, 4 hr contain | Tier 2 |
| **P3 Medium** | Single false negative in jailbreak corpus, elevated dwell time | 4 hr acknowledge, 24 hr resolve | Tier 3 |
| **P4 Low** | Documentation gap, non-production test failure | Next business day | Standard change |

Dwell time SLO: P95 <3600s from incident to alert (`security_dwell_time_seconds`).

---

## Response Workflow

```
Detect → Triage → Contain → Eradicate → Recover → Review
```

1. **Detect:** Prometheus alerts, drift monitor, constitutional classifier metrics
2. **Triage:** Assign severity; check `docs/security/MITRE-ATTACK-COVERAGE.md` for technique mapping
3. **Contain:** Revoke consent, circuit-break agent, route to DLQ
4. **Eradicate:** Deploy hotfix per `docs/GOVERNANCE.md` emergency tiers
5. **Recover:** Verify audit chain, rerun red team corpus
6. **Review:** Post-incident within 48h (Tier 1) or 72h (Tier 2)

---

## Emergency Contacts

| Role | Channel | Backup |
|---|---|---|
| Security On-Call | `#security-oncall` (Slack) | PagerDuty rotation |
| Agent Owner | `#daily-briefing-dev` | Platform lead |
| SRE | `#platform-sre` | Incident commander |

Maintain contact list in internal runbook (not committed — PII).

---

## Parallel Triage

When multiple incidents occur simultaneously, see:

- `docs/security/TABLETOP-EXERCISES.md` — 5-incident scenario
- `docs/security/incident-response-playbook.md` — parallel triage runbook

---

## Related Documents

- `docs/GOVERNANCE.md` — Emergency change authorization tiers
- `docs/RED-TEAMING.md` — Post-incident evaluation protocol
- `docs/OVERRIDE-ROLLBACK.md` — User and operator override paths
- `docs/OBSERVABILITY.md` — Alert definitions and SLOs

---

*Incident Response — Week 7 Gap Remediation*
