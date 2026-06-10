# MITRE ATT&CK Detection Coverage

**Gap #129** | **Week 6 (DB-E128)** | **Last updated:** 2026-06-06

Maps AI Daily Briefing Assistant detections to [MITRE ATT&CK](https://attack.mitre.org/) techniques relevant to agentic systems.

---

## Coverage Summary

| Metric | Target | Source |
|---|---|---|
| Applicable techniques | 20+ | `backend/security/mitre_coverage.py` |
| Coverage ratio | ≥80% | `security_mitre_coverage_ratio` Prometheus gauge |
| Blind spots | Documented + prioritized | This document § Blind Spots |

Run programmatic summary:

```bash
uv run python -c "from backend.security.mitre_coverage import get_coverage_summary; print(get_coverage_summary())"
```

---

## Technique Mapping

| Technique | Name | Tactic | Status | Detection Control |
|---|---|---|---|---|
| T1566.001 | Spearphishing Attachment | Initial Access | ✅ Detected | InputSecurityScanner on calendar text |
| T1566.002 | Spearphishing Link | Initial Access | 🟡 Partial | SSRFValidator + ingestion scan |
| T1190 | Exploit Public-Facing Application | Initial Access | ✅ Detected | Rate limits + circuit breakers |
| T1078 | Valid Accounts | Credential Access | ✅ Detected | JIT CredentialBroker + consent |
| T1550.001 | Application Access Token | Defense Evasion | ✅ Detected | TTL ≤900s credentials |
| T1550.004 | Web Session Cookie | Defense Evasion | 🟡 Partial | Consent expiry audit |
| T1071 | Application Layer Protocol | C2 | ✅ Detected | MCP domain allowlists |
| T1048 | Exfiltration Over Alt Protocol | Exfiltration | ✅ Detected | PII masking + local LLM routing |
| T1498 | Network DoS | Impact | ✅ Detected | Token budgets + rate limits |
| T1499 | Endpoint DoS | Impact | ✅ Detected | Graph circuit breaker |
| T1565 | Data Manipulation | Impact | ✅ Detected | Read-only SQL enforcement |
| T1565.001 | Stored Data Manipulation | Impact | ✅ Detected | Memory quarantine workflow |
| T1213 | Data from Info Repositories | Collection | ✅ Detected | Consent-gated MCP access |
| T1087 | Account Discovery | Discovery | ✅ Detected | EnumerationDetector on consent/credential probes |
| T1059 | Command Interpreter | Execution | N/A | No agent code execution |
| T1027 | Obfuscated Information | Defense Evasion | ✅ Detected | Unicode NFKC normalization |
| T1036 | Masquerading | Defense Evasion | ✅ Detected | Constitutional impersonation rules |
| T1485 | Data Destruction | Impact | ✅ Detected | Delete operations prohibited |
| T1530 | Data from Cloud Storage | Collection | ✅ Detected | Consent-gated calendar reads |
| T1212 | Exploitation for Credential Access | Credential Access | ✅ Detected | Sealed audit log + vault |
| T1195 | Supply Chain Compromise | Initial Access | ✅ Detected | AI-BOM + pip-audit CI |
| T1598 | Phishing for Information | Reconnaissance | ✅ Detected | Spotlighting + constitutional classifiers |

---

## Prometheus Metrics

| Metric | Labels | Purpose |
|---|---|---|
| `security_mitre_detection_total` | `technique_id`, `coverage` | Per-technique detection events |
| `security_mitre_coverage_ratio` | — | Overall coverage gauge |

---

## Blind Spots & Remediation

| Technique | Gap | Planned Remediation |
|---|---|---|
| T1550.004 | Session rotation not enforced in dev | ✅ Per-action authz re-evaluates consent each MCP call (`per_action_authz.py`) |
| T1087 | No active enumeration detection | ✅ EnumerationDetector on consent/credential probes |

---

## Validation Cadence

- **Quarterly:** Re-run coverage summary + update this document
- **On drift alert:** Cross-check affected technique mappings
- **Reference:** `backend/tests/security/test_mitre_coverage.py`

---

*MITRE ATT&CK Coverage — Week 6 Gap Remediation*
