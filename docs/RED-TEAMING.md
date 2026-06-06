# Red Teaming Cadence

**Gap #88** | **Week 6 (DB-E130)** | **OWASP Agent #10 integration**

Continuous adversarial evaluation tied to rogue agent drift detection and constitutional classifier effectiveness.

---

## Triggers

| Severity | Condition | Response SLA |
|---|---|---|
| **Critical** | Long-term drift ratio ≥2× over 7 days | Targeted eval within 4 hours |
| **Warning** | Drift ratio ≥1.5× over 7 days | Scheduled eval within 48 hours |
| **Spike** | 10+ guardrail violations in 1 hour | Emergency review within 1 hour |

Alerts originate from `infrastructure/alerting/drift_detection.yml` and `long_term_drift_ratio` metrics.

---

## Evaluation Protocol

Each red team session includes:

1. **Adversarial prompt testing** — Run `jailbreak_corpus.yaml` against `InputSecurityScanner`; target ≥95% block rate
2. **Version comparison** — Compare current agent prompts vs last known-good git tag
3. **OWASP Agent Top 10 suite** — Verify controls in `backend/security/owasp_agent.py` still map to passing tests
4. **Behavioral consistency** — Edge cases: empty calendar, revoked consent, MCP timeout
5. **Output variance** — Flag hallucination patterns via Critic quality gate

---

## Cadence

| Activity | Frequency | Owner |
|---|---|---|
| Automated jailbreak corpus | Every CI run | `test_jailbreak_corpus.py` |
| Full red team tabletop | Quarterly | Security + Platform |
| MITRE coverage retest | Quarterly | `test_mitre_coverage.py` + doc update |
| Post-incident eval | Within 24h of P1 | On-call + agent owner |

---

## Artifacts

- Corpus: `backend/tests/security/jailbreak_corpus.yaml`
- Results log: `proof/week6/` (and quarterly `proof/red-team-YYYY-QN/`)
- Drift runbook: `docs/OBSERVABILITY.md` § Rogue Agent Drift Detection

---

## Multi-Incident Tabletop (Preview — Week 7)

Week 7 adds Gap #130 five simultaneous incident scenarios. This document establishes the baseline single-track protocol.

---

*Red Teaming Cadence — Week 6 Gap Remediation*
