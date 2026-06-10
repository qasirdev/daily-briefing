# Multi-Incident Tabletop Exercises

**Gap #130** | **Week 7 (DB-E14)**

Quarterly tabletop exercises simulating **five simultaneous incidents** to validate parallel triage capability (Claude Zero-Trust Defensive Operations requirement).

---

## Exercise Objectives

1. Can the team triage 5 incidents concurrently without missing the most critical?
2. Are runbooks clear enough for parallel execution by different responders?
3. Do alerts have proper severity to avoid alert fatigue during multi-incident storms?
4. Does emergency change authorization activate correctly under time pressure?

**Frequency:** Quarterly (aligned with red team cadence in `docs/RED-TEAMING.md`)

---

## Five Simultaneous Incident Scenario

All incidents begin within a 15-minute window during peak briefing usage.

### Incident 1 — Prompt Injection Detected

- **Signal:** `constitutional_violations_total` spike; Critic escalates on calendar event text
- **Severity:** P2
- **Owner:** Security On-Call
- **Runbook:** Block source calendar, rerun `jailbreak_corpus.yaml`, verify spotlighting markers

### Incident 2 — Credential Leak in Logs

- **Signal:** Alert on log pattern matching `access_token` in application logs
- **Severity:** P1
- **Owner:** SRE + Security
- **Runbook:** Tier 1 emergency — rotate credentials via broker, revoke all active consent, verify audit chain

### Incident 3 — Guardrail Violation Spike

- **Signal:** `guardrail_violations_total` >10/hour per `docs/RED-TEAMING.md`
- **Severity:** P2
- **Owner:** Agent Owner
- **Runbook:** Enable circuit breakers, compare 7d vs 30d drift ratio, schedule targeted red team

### Incident 4 — MCP Server Compromise Suspected

- **Signal:** Unexpected tool schema change; tool poisoning validation failure
- **Severity:** P1
- **Owner:** Platform + Security
- **Runbook:** Disable MCP stdio programs in supervisord, fail-closed all external tool calls

### Incident 5 — External Data Source Poisoned

- **Signal:** Memory quarantine triggered; anomalous episodic retrieval scores
- **Severity:** P2
- **Owner:** Data Steward
- **Runbook:** Quarantine affected memory layer, purge user episodic entries, rerun ingestion scan

---

## Triage Priority Matrix

| Priority | Incident | Rationale |
|---|---|---|
| 1 | Incident 2 (credential leak) | Active credential exposure — contain first |
| 2 | Incident 4 (MCP compromise) | Supply chain / tool poisoning — blast radius |
| 3 | Incident 1 (injection) | Active attack vector but contained by classifiers |
| 4 | Incident 5 (memory poison) | Latent spread risk |
| 5 | Incident 3 (guardrail spike) | May be symptom of 1/4/5 |

---

## Exercise Facilitation

1. **T+0:** Facilitator announces all 5 incidents simultaneously
2. **T+15 min:** Each responder states assigned incident + first action
3. **T+45 min:** Cross-check for conflicting actions (e.g., revoking consent while MCP disabled)
4. **T+90 min:** Hotwash — document gaps in runbooks
5. **T+1 week:** Update runbooks and schedule remediation tickets

---

## Success Criteria

- [ ] All 5 incidents documented with owner and first action
- [ ] Priority matrix applied correctly in ≥80% of participant responses
- [ ] Emergency Tier 1 invoked for Incident 2 within simulated 15 min
- [ ] Runbook gaps logged and assigned owners
- [ ] Next quarterly exercise scheduled

---

## Artifacts

Record exercise results in `proof/red-team-YYYY-QN/tabletop-notes.md` (create per quarter).

---

*Multi-Incident Tabletop — Week 7 Gap Remediation*
