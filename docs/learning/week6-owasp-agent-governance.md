# Week 6 Learnings — OWASP Agent Governance & Advanced Defenses

**Date:** 2026-06-06  
**Epic:** DB-E13

---

## Key Implementations

### Multi-Layer Input Scanning

Replaced single-regex Critic scan with `InputSecurityScanner`:
1. **Regex layer** — fast known-signature detection (`PromptInjectionDetector`) with NFKC/base64/hex normalisation and `rapidfuzz` fuzzy matching; **285** payloads in `tests/security/test_injection_payloads.py`, **277** patterns in `security/injection_patterns.py` (inventory synced via `test_corpus_inventory.py`)
2. **ML layer** — Meta LlamaFirewall **PromptGuard 2** (`PromptGuardService`) for semantic jailbreak detection
3. **Constitutional layer** — policy rules from `rules.yaml` (DAN mode, exfiltration, privilege escalation)

Short-circuit: regex hit skips PromptGuard and constitutional evaluation for latency.

### OWASP Agent vs GenAI

GenAI Top 10 covers LLM vulnerabilities; Agent Top 10 adds agent-specific risks (tool misuse, memory poisoning, rogue drift, trust exploitation). Registry in `owasp_agent.py` links each ID to existing controls — minimal new code, maximum audit clarity.

### MITRE ATT&CK for Agentic Systems

22 techniques mapped with `get_coverage_summary()` returning ≥80% ratio. Partial coverage (T1087, T1550.004) documented as Week 7 blind spots.

### Measurement SLOs

- **Dwell time:** `security_dwell_time_seconds` histogram — incident→alert latency
- **Alert coverage:** `security_alert_investigation_coverage` gauge — investigated/total
- **Long-term drift:** extends Week 1 short-term drift with 7d vs 30d ratio

### OWASP Agent #9 — Consent Trust

`ConsentPromptRequest.action_payload` exposes structured JSON (service, scope, agent_id, intent) in the modal — users verify machine action, not just natural-language summary.

---

## Patterns to Reuse

- Rule-based constitutional classifiers before fine-tuned models (95%+ block rate achievable in CI)
- Control registries (`owasp_agent.py`, `mitre_coverage.py`) as single source of truth for compliance docs
- In-process drift monitor for dev; Prometheus gauges for production export

---

## Week 7 Handoff

- AGENT08 partial → full HITL layers
- Multi-incident chaos tabletop (Gap #130)
- Per-action authorization hardening (Gap #128 continuation)

---

*Week 6 Learning Doc — Created 2026-06-06*
