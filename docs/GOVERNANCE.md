# Organizational Governance — AI Daily Briefing Assistant

**Gap #86** | **Week 7 (DB-E14)**

Cross-functional ownership for prompts, models, evaluations, incidents, and emergency changes.

---

## Governance Committee

| Role | Responsibility | Primary Owner |
|---|---|---|
| **Agent Owner** | Prompt versions, agent behavior, regression tests | Platform Engineering |
| **Security Lead** | OWASP compliance, red team cadence, MITRE coverage | Security |
| **Data Steward** | Consent records, memory quarantine, RLS policies | Data Platform |
| **SRE / On-Call** | SLOs, drift alerts, incident triage | Platform SRE |
| **Product Owner** | HITL policy, user-facing consent UX | Product |

**Cadence:** Monthly governance review; quarterly red team + tabletop exercise.

---

## Asset Ownership

| Asset | Owner | Review Frequency |
|---|---|---|
| Agent prompts (`prompts/`) | Agent Owner | Every prompt version bump |
| LLM model selection | Agent Owner + Security | Quarterly |
| Evaluation corpora | Security | Every red team cycle |
| AI-BOM (`infrastructure/ai-bom.yaml`) | Security | Weekly CI validation |
| Vendor assessments | Security | 6-month re-assessment |

---

## Emergency Change Authorization (Gap #131)

Normal change approval (2-week cycle) is insufficient during active exploitation. Pre-established tiers:

### Tier 1 — Immediate (Security Team)

- **Authority:** Deploy hotfixes without prior approval
- **Retrospective review:** Within 48 hours
- **Triggers:** Active prompt injection exploitation, credential leak in production logs
- **Guardrails:** All changes logged in sealed audit chain; revert if retrospective fails

### Tier 2 — Expedited (4 Hours)

- **Authority:** Security Lead + one executive approver
- **Triggers:** CVSS ≥9 affecting production agents, guardrail violation spike (>10/hr)
- **Guardrails:** Post-incident review within 72 hours

### Tier 3 — Expedited (24 Hours)

- **Authority:** Full governance committee (async vote)
- **Triggers:** Data breach suspicion, MCP server compromise, multi-incident tabletop failure
- **Guardrails:** Document in `docs/adr/` within 5 business days

---

## Deployment Gates

Production deploys require:

- [ ] `uv run pytest` — full suite green
- [ ] OWASP Agent Top 10 controls implemented (no `partial` on P0 IDs)
- [ ] MITRE coverage ratio ≥80%
- [ ] Jailbreak corpus block rate ≥95%
- [ ] Alert investigation coverage >95% (rolling 7d)

See `docs/INCIDENT-RESPONSE.md` for incident procedures referencing these tiers.

---

## Configuration Integrity

- Agent configs version-controlled in `prompts/` with CHANGELOG.md per agent
- Docker images signed via Cosign (MVP 6)
- Audit log hash chain verified on deploy (`verify_audit_chain()`)

---

*Organizational Governance — Week 7 Gap Remediation*
