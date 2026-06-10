# Production Gap Analysis Review — Post-Remediation Production Readiness

**Date:** June 7, 2026  
**Specification:** `007-01-ai-daily-briefing-assistant-v2.0.0.md`  
**Baseline:** Gap remediation Weeks 1–8 complete (DB-E8 through DB-E15)  
**Test Baseline:** 436 passed, 3 skipped (`docs/tasks/todo.md`)  
**Prior Analysis:** `docs/gaps/GAP-ANALYSIS-REVIEW.md` (121 gaps, June 4–6, 2026)

**Guidance Sources:**
- `007-01-ai-daily-briefing-assistant-v2.0.0.md` — Production-ready architecture spec
- `AGENT.md` — Root workflow and MVP status
- `docs/DEPLOYMENT-GATES.md` — Metric-based release criteria
- `docs/gaps/PROMPT-ENGINEERING-REMEDIATION.md` — Prompt v2 migration status

**Related (to be created):**
- `docs/gaps/production/PROD-PROPOSAL-REVIEW-SUMMARY.md`
- `docs/gaps/production/PROD-KICKOFF-PROMPT.md`
- `docs/gaps/production/PROD-WEEK{n}-IMPLEMENTATION-GUIDE.md` (per week)
- `docs/jira-tickets-json/DB-E16-production-week1.json` (and subsequent epics)

---

## Executive Summary

This document reviews the **current codebase state** (after 8 weeks of gap remediation) against the **v2.0.0 production specification** and identifies **remaining production gaps** that must be closed before a safe, scalable production launch.

The original `GAP-ANALYSIS-REVIEW.md` tracked 121 gaps from proposal review (IBM + Claude Zero-Trust). Weeks 1–8 addressed the majority of those gaps at the **building-block level** — agents, memory, consent, supply chain, observability metrics, and tests exist. This production review focuses on what is **not yet wired, enabled, or hardened** for real production traffic.

**Status Overview (53 production gaps):**

| Status | Count | % |
|---|---|---|
| ✅ **Production Ready** | 8 | 15% |
| 🟡 **Partially Ready** | 20 | 38% |
| 🔴 **Not Production Ready** | 25 | 47% |

**Priority Breakdown:**

| Priority | Count | Meaning |
|---|---|---|
| **P0 (Critical)** | 14 | Block production launch |
| **P1 (High)** | 24 | Required before scaling users |
| **P2 (Medium)** | 15 | Enterprise extras — defer post-launch acceptable with documented risk |

**Critical Finding:** The application can generate briefings end-to-end today, but **production operations infrastructure is incomplete**. Code-level security (consensus, spotlighting, validation) exists but is disabled. **Operational gaps** include: no staging environment, no disaster recovery, no production runbooks, no health checks beyond metrics, no TLS configuration, no automated backups, no load testing, and incomplete monitoring alerting.

**Estimated Effort:** 11 production weeks (PROD Week 1–9) for P0 + P1; P2 as post-launch backlog with documented risk acceptance.

---

## Context: What Changed Since Original Gap Review

### Completed in Gap Remediation (Weeks 1–8)

| Area | Original Gap Status | Current State |
|---|---|---|
| Multi-agent verification (Gaps #1–7) | 🔴 Not Implemented | 🟡 Built, feature-flagged off |
| CoALA memory (Gaps #8–13) | 🔴 Not Implemented | ✅ Four layers + agentic RAG |
| JIT credentials (Gap #19) | 🔴 Not Implemented | ✅ `backend/security/vault.py` |
| Agentic consent (Gaps #31–32) | 🟡 Partial | ✅ Full consent + per-action authz |
| AI-BOM (Gap #115) | 🔴 Not Implemented | ✅ `infrastructure/ai-bom.yaml` + CI |
| Constitutional classifiers (Gap #126) | 🔴 Not Implemented | 🟡 Critic path only |
| MITRE ATT&CK (Gap #129) | 🔴 Not Implemented | 🟡 Registry + metrics, no dashboard |
| Dwell Time SLO (Gap #134) | 🔴 Not Implemented | 🟡 Metric exists, no Grafana panel |
| RAG poisoning (Gap #120) | 🔴 Not Implemented | ✅ Quarantine + source validation |
| Prompt caching | 🔴 Not Implemented | ✅ Cache + warmer + metrics |
| DLQ routing | ✅ Implemented | ✅ Wired in graph |
| Cosign signing | — | ✅ `docker-publish.yml` |
| Deployment gates (Gap #59) | 🔴 Not Implemented | 🟡 Code exists, not in CI |
| NHI registry (Gaps #92–93) | 🔴 Not Implemented | 🟡 JSON registry, 5 agents, no X.509 |
| Prompt v2 (Gap #136) | 🟡 Focus only | 🟡 4/7 agents on v2 structure |

### Doc Drift to Resolve

| Document | Issue |
|---|---|
| `AGENT.md` | Marks MVPs 1–6 ✅ but predates v2.0.0 production checklist |
| `007-01-ai-daily-briefing-assistant-v2.0.0.md` | MVP table still shows "Planned" — superseded by implementation |
| `docs/PLAN.md` | MVPs 3–5 header shows 🔄 though tasks are ✅ |
| `docs/tasks/checkpoint.md` | Stale (pre–Week 1 kickoff) |
| `.env.production.example` | `ENABLE_CONSENSUS_WORKFLOW=false` |

---

## Critical Gaps Requiring Immediate Action (P0)

### 1. Consensus Workflow Not Enabled in Production (PROD-001)

**Maps to:** Gaps #1–7, #83  
**Current State:** Verification, Adversarial, and Consensus agents exist and are tested (`backend/tests/architecture/test_consensus.py`), but `enable_consensus_workflow` defaults to `False` in `backend/settings.py` and `.env.production.example`.

**Production Risk:** Production runs legacy Focus → Critic path, skipping IBM Generator → Verification → Adversarial → Consensus pattern. Multi-agent cross-validation is dormant.

**Required Changes:**
- Set `ENABLE_CONSENSUS_WORKFLOW=true` in production env
- Validate P95 latency SLO (<10s briefing generation) under consensus path
- Document rollback procedure (flip flag to `false`)
- Run staging soak test with real LLM keys before promotion

**Impact:** Critical — Core v2.0.0 reliability architecture inactive  
**Files to Update:**
- `.env.production.example`
- `docs/guidence/docker-setup.md`
- `docs/ARCHITECTURE.md` (production default section)
- `backend/settings.py` (document production override)

---

### 2. Runtime Spotlighting Not Implemented (PROD-002)

**Maps to:** Gap #114  
**Current State:** Spotlighting documented in `prompts/focus/input-security.md` (352 lines) but **no runtime implementation** in `backend/`. No `<<<EXTERNAL_CONTENT>>>` wrapping. Focus agent uses `<user_data>` tags (`backend/agents/focus/node.py`), not spec markers. Grep for `EXTERNAL_CONTENT` or `spotlight` in `backend/` returns zero matches.

**Production Risk:** Indirect injection via calendar events, task titles, and MCP responses remains exploitable despite prompt documentation. Spec target: >50% → <2% injection success rate requires **runtime** enforcement.

**Required Changes:**
- Create `backend/security/spotlighting.py` with `spotlight_external_content()`
- Apply to all MCP responses before agent consumption (task, calendar, focus)
- Apply to RAG/memory retrieval output in `retrieve_agent_memory()`
- Load `input-security.md` rules into prompt assembly where applicable
- Add `backend/tests/security/test_spotlighting.py` (injection corpus)

**Impact:** Critical — P0 Claude Zero-Trust control  
**Files to Create/Update:**
- `backend/security/spotlighting.py` (NEW)
- `backend/agents/task/node.py`
- `backend/agents/calendar/node.py`
- `backend/agents/focus/node.py`
- `backend/memory/agentic_rag.py`
- `backend/mcp/client.py` (wrap responses at boundary)
- `docs/SECURITY.md`

---

### 3. MCP Tool Poisoning Defense Layer Missing (PROD-003)

**Maps to:** Gap #117  
**Current State:** SSRF allowlist and SQL table allowlist exist in `backend/mcp/client.py`. Spec requires `backend/mcp/validator.py` with `MCPResponseValidator` — schema validation, output sanitization (nh3), injection detection, business logic checks, anomaly detection. **File does not exist.**

**Production Risk:** Compromised or malicious MCP server responses can manipulate agents without validation layer.

**Required Changes:**
- Create `backend/mcp/validator.py` with three-layer defense (schema, sanitization, anomaly)
- Wire validator into all MCP `call_tool()` return paths
- Enforce tool allowlist per agent (calendar: `read_events`, task: `list`/`update`)
- Add tool-chaining counter (max 3 sequential calls — see PROD-019)
- Add `backend/tests/security/test_tool_poisoning.py`

**Impact:** Critical — MCP supply chain attack surface  
**Files to Create/Update:**
- `backend/mcp/validator.py` (NEW)
- `backend/mcp/client.py`
- `backend/mcp/postgres.py`, `calendar_stdio.py`
- `docs/MCP.md`

---

### 4. Deployment Gates Not in Release CI (PROD-004)

**Maps to:** Gap #59  
**Current State:** `check_deployment_gates()` implemented in `backend/observability/deployment_gates.py` with tests. `docs/DEPLOYMENT-GATES.md` explicitly states CI integration is TODO. Not present in `.github/workflows/ci.yml` or `docker-publish.yml`.

**Production Risk:** Images can be promoted without MITRE coverage, alert investigation, agentic RAG, or compression budget validation.

**Required Changes:**
- Add CI job: `APP_ENV=production uv run python -c "from backend.observability.deployment_gates import check_deployment_gates; ..."`
- Require `all_pass=True` before image promotion in `docker-publish.yml`
- Fail release on gate failure (not warn-only in production)
- Document gate overrides in `docs/GOVERNANCE.md`

**Impact:** Critical — No automated production readiness gate  
**Files to Update:**
- `.github/workflows/ci.yml`
- `.github/workflows/docker-publish.yml`
- `docs/DEPLOYMENT-GATES.md`

---

### 5. Production Environment Defaults Misaligned (PROD-005)

**Maps to:** Gaps #1–7, #59, spec deployment section  
**Current State:** `.env.production.example` has consensus off, and observability verify checklist (`docs/guidence/observability/05-verify-before-kickoff.md`) still recommends `ENABLE_CONSENSUS_WORKFLOW=false`.

**Production Risk:** Copy-paste production deploy inherits development-safe defaults, not production-hardened configuration.

**Required Changes:**
- Update `.env.production.example` with production-recommended values
- Create production config checklist (consensus, agentic RAG, compression, OTEL)
- Align observability kickoff docs with production targets
- Add `docs/guidence/production-deployment.md` (or section in docker-setup)

**Impact:** Critical — Configuration drift at deploy time  
**Files to Update:**
- `.env.production.example`
- `docs/guidence/observability/05-verify-before-kickoff.md`
- `docs/guidence/docker-setup.md`

---

## Detailed Gap Tracking

### P0 — Production Launch Blockers

| PROD # | Description | Maps to | Status | Priority |
|---|---|---|---|---|
| PROD-001 | Enable consensus workflow in production | Gaps #1–7 | 🟡 Built, off by default | P0 |
| PROD-002 | Runtime spotlighting for all external data | Gap #114 | 🔴 Not Implemented | P0 |
| PROD-003 | MCP response validator (`mcp/validator.py`) | Gap #117 | 🔴 Not Implemented | P0 |
| PROD-004 | Deployment gates in release CI | Gap #59 | 🟡 Code only | P0 |
| PROD-005 | Production env defaults aligned with v2.0.0 | — | 🟡 Misaligned | P0 |

### P1 — Scale-Ready Hardening

| PROD # | Description | Maps to | Status | Priority |
|---|---|---|---|---|
| PROD-006 | Prompt v2 migration — Task Agent | Gap #136 | 🟡 6-file legacy | P1 |
| PROD-007 | Prompt v2 migration — Calendar Agent | Gap #136 | 🟡 6-file legacy | P1 |
| PROD-008 | Prompt v2 migration — Orchestrator Agent | Gap #136 | 🟡 6-file legacy | P1 |
| PROD-009 | Load `input-security.md` in prompt assembly | Gap #136, #114 | 🟡 File exists, not loaded | P1 |
| PROD-010 | Constitutional classifiers on all LLM I/O | Gap #126 | 🟡 Critic only | P1 |
| PROD-011 | NHI registry — add verification + adversarial agents | Gaps #92–93 | 🟡 5 of 7 agents | P1 |
| PROD-012 | NHI runtime identity propagation | Gaps #92–93 | 🟡 Metadata only | P1 |
| PROD-013 | Redis for working memory TTL + credential cache | Gaps #8, #19 | 🔴 Not Implemented | P1 |
| PROD-014 | Grafana — prompt cache performance panels | Spec cache dashboard | 🟡 Metrics only | P1 |
| PROD-015 | Grafana — dwell time SLO panels | Gap #134 | 🟡 Metric only | P1 |
| PROD-016 | Grafana — MITRE coverage dashboard | Gap #129 | 🟡 Registry only | P1 |
| PROD-017 | OpenSSF Scorecard automated in CI | Gap #116 | 🟡 Manual/docs only | P1 |
| PROD-018 | Agent OS Kernel unified module | Gaps #27–29 | 🟡 Distributed | P1 |

### P1 (Continued) — Operational Readiness

| PROD # | Description | Maps to | Status | Priority |
|---|---|---|---|---|
| PROD-029 | **Load testing at production scale** | Spec performance | 🔴 Not Implemented | P0 |
| PROD-030 | Disaster recovery procedures (RTO/RPO) | Operations | 🔴 Not Implemented | P1 |
| PROD-031 | Production runbooks (incident response) | Operations | 🔴 Not Implemented | P1 |
| PROD-032 | **Deep health checks** (DB, Redis, MCP, LLM) | Spec monitoring | 🔴 Not Implemented | P0 |
| PROD-033 | Automated secret rotation | Gap #19 | 🔴 Not Implemented | P1 |
| PROD-034 | **Database migration strategy** (zero-downtime) | Operations | 🔴 Not Implemented | P0 |
| PROD-035 | Production rate limiting (per-user/IP/agent) | Spec performance | 🔴 Not Implemented | P1 |
| PROD-036 | **CORS configuration** (production allowlist) | Operations | 🔴 Not Implemented | P0 |
| PROD-037 | **SSL/TLS configuration** (TLS 1.3, cert management) | Operations | 🔴 Not Implemented | P0 |
| PROD-038 | Monitoring alerts (PagerDuty/Opsgenie) | Spec observability | 🔴 Not Implemented | P1 |
| PROD-039 | Log aggregation (Loki/CloudWatch) | Spec observability | 🔴 Not Implemented | P1 |
| PROD-043 | SLA/SLO documentation (formal agreements) | Operations | 🔴 Not Implemented | P1 |

### P1 (Continued) — Infrastructure Hardening

| PROD # | Description | Maps to | Status | Priority |
|---|---|---|---|---|
| PROD-044 | Network segmentation (VPC, firewall rules) | Operations | 🔴 Not Implemented | P1 |
| PROD-045 | Container security (Falco, Trivy, non-root) | Gap #116 | 🔴 Not Implemented | P1 |
| PROD-046 | **Backup strategy** (DB, Redis, config, 30-day) | Operations | 🔴 Not Implemented | P0 |
| PROD-047 | **Rollback procedures** (blue-green, canary) | Operations | 🔴 Not Implemented | P0 |
| PROD-048 | Session management (TTL, refresh tokens) | Operations | 🔴 Not Implemented | P1 |

### P1 (Continued) — Testing & Validation

| PROD # | Description | Maps to | Status | Priority |
|---|---|---|---|---|
| PROD-049 | **Staging environment** (production-like) | Operations | 🔴 Not Implemented | P0 |
| PROD-050 | **Smoke tests** (post-deployment validation) | Operations | 🔴 Not Implemented | P0 |
| PROD-051 | Load testing in CI (k6/Locust, regression) | Spec performance | 🔴 Not Implemented | P1 |
| PROD-052 | Security scanning (DAST, penetration testing) | Gap #116 | 🔴 Not Implemented | P1 |

### P2 — Enterprise Extras (Post-Launch Acceptable)

| PROD # | Description | Maps to | Status | Priority |
|---|---|---|---|---|
| PROD-019 | Delegation-token format on all external calls | Gap #118 | 🟡 Consent broker partial | P2 |
| PROD-020 | Tool-chaining policy (max 3 sequential MCP calls) | Gap #117 | 🔴 Not Implemented | P2 |
| PROD-021 | MCP sandbox resource limits (CPU/memory/network) | Gaps #28–29 | 🔴 Not Implemented | P2 |
| PROD-022 | Agent configuration cryptographic signing | Gap #86 | 🔴 Not Implemented | P2 |
| PROD-023 | Production Vault backend (not dev broker) | Gap #19, ADR | 🟡 Dev broker | P2 |
| PROD-024 | NHI X.509 PKI (vs JSON metadata registry) | Gaps #92–93, #125 | 🔴 Not Implemented | P2 |
| PROD-025 | Hardware-backed identity (HSM/TPM) | Gap #124 | 🔴 Not Implemented | P2 |
| PROD-026 | Alert investigation workflow automation | Gap #135 | 🟡 Metric only | P2 |
| PROD-027 | Multi-worker prompt cache coordination | Spec caching | 🟡 Single-process | P2 |
| PROD-028 | Chaos testing in CI (5 simultaneous incidents) | Gap #130 | 🟡 Tabletop doc only | P2 |
| PROD-040 | API documentation (OpenAPI, Swagger UI) | Operations | 🔴 Not Implemented | P2 |
| PROD-041 | User documentation (setup, troubleshooting) | Operations | 🟡 Partial | P2 |
| PROD-042 | Compliance documentation (SOC 2, ISO 27001) | Operations | 🔴 Not Implemented | P2 |
| PROD-053 | Chaos engineering in staging | Gap #130 | 🔴 Not Implemented | P2 |

### Already Production Ready

| Area | Evidence | Status |
|---|---|---|
| Core briefing pipeline | LangGraph + 6 agents + API | ✅ |
| Agentic consent + JIT broker | `vault.py`, `consent.py`, calendar gate | ✅ |
| DLQ routing | `dlq_handler.py`, `dlq/store.py` | ✅ |
| Local LLM fallback | `llm/router.py` | ✅ |
| Prompt caching + warming | `prompt_cache.py`, `main.py` startup | ✅ |
| RAG quarantine + source validation | `memory/quarantine.py`, `source_validation.py` | ✅ |
| AI-BOM + Cosign | `ai-bom.yaml`, CI validation, `docker-publish.yml` | ✅ |
| OpenTelemetry + Prometheus base | `observability/metrics.py`, `/metrics` | ✅ |
| Test suite | 436 passed | ✅ |

---

## Gap Detail — P1 Items

### PROD-006–008: Prompt v2 Migration (Task, Calendar, Orchestrator)

**Current State:** Focus, verification, adversarial, and critic have v2 11-file structure. Task, calendar, orchestrator retain legacy 6-file layout (`system.md`, `tools.md`, `skills.md`, `guardrails.md`, `CHANGELOG.md`, `CONTRACT.md`).

**Required per agent:**
```
prompts/{agent}/
├── system.md, context.md, instructions.md, examples.md
├── output-schema.md, tools.md, reasoning.md, guardrails.md
├── input-security.md, quality-checklist.md
├── CHANGELOG.md, CONTRACT.md
```

**Reference:** `prompts/focus/` (13 files), `docs/PROMPT-ENGINEERING-GUIDE.md`

**Success Criteria:**
- [ ] 3–5 examples with `<thinking>` per agent
- [ ] `prompt_version` bumped in envelope metadata
- [ ] Prompt loader (`backend/prompts_loader.py`) assembles v2 files
- [ ] Accuracy regression tests per agent

---

### PROD-009: Load input-security.md at Runtime

**Current State:** `V2_STATIC_FILES` in `backend/prompts_loader.py` does not include `input-security.md`. Security rules exist in markdown only.

**Required:** Add `input-security.md` to static assembly for all v2 agents; ensure spotlighting rules reach LLM context.

---

### PROD-010: Constitutional Classifiers — Full Coverage

**Current State:** `backend/security/constitutional_classifier.py` wired via `InputSecurityScanner` in critic agent only (`backend/agents/critic/node.py`).

**Required:** Scan all LLM inputs (user request, MCP-assembled context) and outputs (all agent envelopes) per spec (>95% jailbreak block target).

---

### PROD-011–012: NHI Registry Completion

**Current State:** `backend/security/nhi_registry.json` registers 5 agents. Tests expect 5, not 7 (`test_nhi.py`). No X.509. Registry not checked at agent invocation time.

**Required:**
- Add `verification` and `adversarial` to registry
- Propagate `agent_identity` in envelope metadata at runtime
- Document X.509 as P2 (PROD-024) with JSON acceptable for initial production

---

### PROD-013: Redis Integration

**Current State:** Spec requires PostgreSQL + Redis for working memory and credential TTL cache. No Redis in docker-compose or code. Working memory is LangGraph state only.

**Required:**
- Add Redis to `docker-compose.yml` and production compose
- Working memory TTL cache in `backend/memory/working.py`
- Short-lived credential cache in `backend/security/vault.py`
- Document in `docs/adr/` (extends Week 5 ADR)

---

### PROD-014–016: Observability Dashboards

**Current State:** Metrics exported (`security_dwell_time_seconds`, `llm_cache_hits_total`, `security_mitre_coverage_ratio`). `infrastructure/monitoring/grafana-slo-dashboard.json` has availability/latency/error only.

**Required Grafana panels:**
- Cache hit rate (target >70%)
- Tokens saved / cost savings (24h)
- Dwell time P95 (target <3600s)
- MITRE coverage ratio (target ≥0.80)
- Cache hit rate by agent

**Reference:** Spec § Prompt Caching Performance Dashboard, `docs/guidence/observability/`

---

### PROD-017: OpenSSF Scorecard in CI

**Current State:** `openssf_scorecard_minimum()` in `backend/security/bom.py`; policy in `docs/SUPPLY-CHAIN-SECURITY.md`. CI runs `pip-audit` and AI-BOM validation, not `ossf-scorecard`.

**Required:** Add scorecard job to CI (threshold ≥7.0) or documented waiver with manual review gate.

---

### PROD-018: Agent OS Kernel

**Current State:** Capabilities distributed — LangGraph (scheduler), `backend/memory/*` (memory manager), `backend/mcp/client.py` (tool manager), `vault.py` + `nhi_registry.py` (identity), `drift_monitor.py` (security monitor). No `backend/kernel/` module.

**Required:** Either extract unified `backend/kernel/` with explicit interfaces, or document distributed architecture as accepted production pattern in `docs/AGENT-OS-KERNEL.md` with operational runbooks.

---

## Operational Readiness Gaps (PROD-029 through PROD-053)

### PROD-029: Load Testing at Production Scale ⚠️ **P0**

**Current State:** No load testing. Performance validated only via manual single-user tests.

**Production Risk:** Unknown behavior under concurrent load. Potential cascading failures, resource exhaustion, or latency spikes at scale.

**Required Changes:**
- Implement load testing with k6 or Locust
- Test scenarios: 10 concurrent users, 100 concurrent users, 1,000 requests/hour
- Validate SLOs: P95 latency <10s, P99 latency <30s
- Test MCP timeout handling, Redis connection pooling, DB connection limits
- Test prompt cache hit rates under concurrent load
- Document performance baseline and scaling limits

**Impact:** Critical — Unknown production capacity  
**Success Criteria:**
- [ ] Load test suite for 10/100/1000 concurrent users
- [ ] All SLOs validated under load
- [ ] Resource limits documented (max concurrent requests)
- [ ] Graceful degradation tested (LLM API rate limits)

---

### PROD-030: Disaster Recovery Procedures

**Current State:** No formal DR plan. No documented RTO/RPO targets.

**Production Risk:** Data loss or extended downtime during infrastructure failures.

**Required Changes:**
- Define RTO (Recovery Time Objective): Target 4 hours
- Define RPO (Recovery Point Objective): Target 1 hour (max data loss)
- Document backup restoration procedures
- Test DR scenarios: DB corruption, region failure, credential compromise
- Automate backup verification (restore to staging weekly)
- Document escalation paths and on-call procedures

**Impact:** High — Business continuity  
**Files to Create:**
- `docs/operations/DISASTER-RECOVERY.md`
- `docs/operations/BACKUP-RESTORATION.md`

---

### PROD-031: Production Runbooks

**Current State:** No incident response runbooks. Troubleshooting is ad-hoc.

**Production Risk:** Slow incident resolution, inconsistent responses, knowledge loss.

**Required Changes:**
Create runbooks for common production incidents:
- **MCP Timeout:** PostgreSQL MCP unresponsive
- **LLM API Down:** OpenAI/Anthropic API outage
- **High Latency:** P95 latency >20s
- **Database Connection Exhausted:** Connection pool full
- **Redis Down:** Working memory cache unavailable
- **Consensus Failure:** Verification/adversarial agent disagreement
- **DLQ Backlog:** Dead letter queue >100 entries
- **Security Alert:** Injection attempt detected

**Impact:** High — Operational efficiency  
**Files to Create:**
- `docs/operations/runbooks/MCP-TIMEOUT.md`
- `docs/operations/runbooks/LLM-API-DOWN.md`
- `docs/operations/runbooks/HIGH-LATENCY.md`
- `docs/operations/runbooks/DATABASE-CONNECTION-EXHAUSTED.md`
- `docs/operations/runbooks/REDIS-DOWN.md`
- `docs/operations/runbooks/CONSENSUS-FAILURE.md`
- `docs/operations/runbooks/DLQ-BACKLOG.md`
- `docs/operations/runbooks/SECURITY-ALERT.md`

---

### PROD-032: Deep Health Checks ⚠️ **P0**

**Current State:** `/metrics` endpoint only. No dependency health checks.

**Production Risk:** Load balancer routes traffic to unhealthy instances. Silent failures.

**Required Changes:**
```python
# backend/api/v1/health.py
@router.get("/health")
async def health_check():
    """Shallow health check for load balancer."""
    return {"status": "healthy"}

@router.get("/health/deep")
async def deep_health_check():
    """Deep health check for all dependencies."""
    checks = {
        "database": await check_database(),      # SELECT 1
        "redis": await check_redis(),            # PING
        "mcp_postgres": await check_mcp_postgres(),  # List tables
        "mcp_calendar": await check_mcp_calendar(),  # Stub call
        "llm_primary": await check_llm(router.primary_model),
        "llm_fallback": await check_llm(router.fallback_model),
    }
    all_healthy = all(c["status"] == "healthy" for c in checks.values())
    status_code = 200 if all_healthy else 503
    return JSONResponse(
        content={"status": "healthy" if all_healthy else "degraded", "checks": checks},
        status_code=status_code
    )
```

**Impact:** Critical — Production health visibility  
**Files to Update:**
- `backend/api/v1/health.py`
- `docker-compose.yml` (healthcheck configuration)
- `docs/operations/HEALTH-CHECKS.md`

---

### PROD-033: Automated Secret Rotation

**Current State:** Secrets rotated manually. No automation or expiry tracking.

**Production Risk:** Stale credentials, credential sprawl, compliance gaps.

**Required Changes:**
- Implement secret rotation for: DB passwords, Redis passwords, API keys, OAuth refresh tokens
- Rotation schedule: 90 days for long-lived, 15 minutes for JIT credentials
- Track secret age in Vault metadata
- Alert on secrets >80 days old (10-day warning window)
- Automate rotation during off-peak hours
- Test zero-downtime rotation (blue-green credential switch)

**Impact:** High — Security hygiene  
**Files to Create:**
- `backend/security/secret_rotation.py`
- `docs/operations/SECRET-ROTATION.md`

---

### PROD-034: Database Migration Strategy ⚠️ **P0**

**Current State:** Alembic migrations exist but no production strategy.

**Production Risk:** Breaking schema changes, downtime during migrations, rollback failures.

**Required Changes:**
- Define migration safety rules: Additive-only (add columns, tables), no data migrations in schema
- Test migrations on staging with production data volume
- Implement rollback procedure (downgrade script + data reconciliation)
- Automate migration on deploy: `alembic upgrade head` in supervisord startup
- Add migration health check: Compare schema version in DB vs code
- Document migration rollback procedure

**Impact:** Critical — Zero-downtime deployments  
**Files to Create:**
- `docs/operations/DATABASE-MIGRATIONS.md`
- `backend/scripts/pre_deploy_migration_check.py`

---

### PROD-035: Production Rate Limiting

**Current State:** Token budgets only. No user/IP/agent rate limits.

**Production Risk:** API abuse, credential stuffing, DoS attacks.

**Required Changes:**
```python
# backend/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to briefing endpoint
@router.post("/briefing")
@limiter.limit("10/minute")  # 10 requests per minute per IP
@limiter.limit("100/hour")   # 100 requests per hour per IP
async def generate_briefing(request: Request, ...):
    ...
```

**Limits:**
- Per IP: 10 requests/minute, 100 requests/hour
- Per user: 50 requests/hour
- Per agent (internal): No limit (authenticated via NHI)
- Burst allowance: 2x rate for 30 seconds

**Impact:** High — API protection  
**Files to Update:**
- `backend/middleware/rate_limit.py`
- `backend/main.py` (register middleware)
- `docs/API.md` (document rate limits)

---

### PROD-036: CORS Configuration ⚠️ **P0**

**Current State:** CORS likely misconfigured or wide-open (`allow_origins=["*"]`).

**Production Risk:** Cross-site attacks, data leakage to untrusted origins.

**Required Changes:**
```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.dailybriefing.ai",
        "https://staging.dailybriefing.ai",
        # NO wildcards in production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)
```

**Impact:** Critical — Security boundary  
**Files to Update:**
- `backend/main.py`
- `.env.production.example` (document CORS_ORIGINS)
- `docs/SECURITY.md`

---

### PROD-037: SSL/TLS Configuration ⚠️ **P0**

**Current State:** No TLS in local dev. Production TLS configuration not documented.

**Production Risk:** Man-in-the-middle attacks, credential interception.

**Required Changes:**
- Configure TLS 1.3 in nginx
- Obtain SSL certificates: Let's Encrypt (free, auto-renew) or AWS ACM
- Enforce HTTPS redirects (HTTP → HTTPS)
- Enable HSTS header: `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- Configure secure ciphers: `ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512`
- Test with SSL Labs (target A+ rating)

**Impact:** Critical — Transport security  
**Files to Update:**
- `infrastructure/nginx.conf`
- `docs/operations/TLS-SETUP.md`
- `docker-compose.production.yml` (certbot service)

---

### PROD-038: Monitoring Alerts

**Current State:** Metrics exported, but no alerting configured.

**Production Risk:** Incidents go unnoticed until user reports.

**Required Changes:**
- Integrate PagerDuty or Opsgenie
- Configure alert rules in Prometheus:
  - P95 latency >10s for 5 minutes → Page on-call
  - Error rate >5% for 2 minutes → Page on-call
  - DLQ size >50 → Warn
  - Security violation detected → Page immediately
  - Dwell time >1 hour → Page immediately
  - Consensus disagreement rate >10% → Warn
  - Prompt cache hit rate <70% for 10 minutes → Warn
- Define escalation policy: On-call → Manager → VP Engineering
- Test alert delivery weekly

**Impact:** High — Incident response  
**Files to Create:**
- `infrastructure/monitoring/prometheus-alerts.yml`
- `docs/operations/ALERTING.md`
- `docs/operations/ON-CALL.md`

---

### PROD-039: Log Aggregation

**Current State:** Logs in stdout only. No centralized search or retention.

**Production Risk:** Lost logs on container restart. No ability to search across instances.

**Required Changes:**
- Deploy Loki (Grafana) or use CloudWatch Logs
- Configure log shipping: Docker → Promtail → Loki
- Retention policy: 30 days (standard), 1 year (audit logs)
- Index critical fields: `trace_id`, `user_id`, `agent_id`, `status`
- Enable log-based alerts: Error rate, security violations
- Document log search queries for common investigations

**Impact:** High — Debugging and forensics  
**Files to Create:**
- `infrastructure/monitoring/loki-config.yml`
- `infrastructure/monitoring/promtail-config.yml`
- `docs/operations/LOG-AGGREGATION.md`

---

### PROD-040: API Documentation

**Current State:** No API documentation. Frontend and agents use implicit contracts.

**Production Risk:** Integration errors, breaking changes unnoticed.

**Required Changes:**
- Generate OpenAPI spec from FastAPI routes
- Deploy Swagger UI at `/docs`
- Document request/response schemas, error codes, rate limits
- Add versioning strategy: `/v1/briefing`, `/v2/briefing`
- Document deprecation policy: 6-month notice before removal
- Auto-generate docs in CI (fail if spec changes without version bump)

**Impact:** Medium — Developer experience  
**Files to Update:**
- `backend/main.py` (enable Swagger UI)
- `docs/API.md`

---

### PROD-041: User Documentation

**Current State:** Partial setup docs. No user-facing documentation.

**Production Risk:** Support load, poor UX, adoption friction.

**Required Changes:**
Create user documentation:
- **Setup Guide:** Account creation, OAuth flow, first briefing
- **Troubleshooting:** Calendar not syncing, no tasks visible, briefing empty
- **FAQ:** How to revoke consent, how to export data, privacy policy
- **Admin Manual:** User management, audit logs, configuration

**Impact:** Medium — User success  
**Files to Create:**
- `docs/user-guide/SETUP.md`
- `docs/user-guide/TROUBLESHOOTING.md`
- `docs/user-guide/FAQ.md`
- `docs/admin-guide/USER-MANAGEMENT.md`

---

### PROD-042: Compliance Documentation

**Current State:** No compliance documentation. Audit trail exists but not documented.

**Production Risk:** Failed audits, compliance violations, customer trust loss.

**Required Changes (if SOC 2 / ISO 27001 required):**
- Document data flows: Where PII lives, retention, deletion
- Document access controls: Who can access what, how, audit trails
- Document incident response procedures
- Document security controls: Encryption at rest/transit, key management
- Create evidence for audit: Logs, policies, training records
- Engage third-party auditor (6-month lead time)

**Impact:** Medium (P2 unless regulated industry)  
**Files to Create:**
- `docs/compliance/DATA-FLOWS.md`
- `docs/compliance/ACCESS-CONTROLS.md`
- `docs/compliance/INCIDENT-RESPONSE.md`
- `docs/compliance/SECURITY-CONTROLS.md`

---

### PROD-043: SLA/SLO Documentation

**Current State:** Metrics tracked, but no formal SLAs communicated.

**Production Risk:** Customer expectations misaligned, no accountability.

**Required Changes:**
Define and document SLAs:
- **Uptime:** 99.9% monthly (43 minutes downtime allowed)
- **Latency:** P95 <10s, P99 <30s
- **Support Response:** Critical 1 hour, High 4 hours, Medium 24 hours
- **Incident Updates:** Every 30 minutes during outage
- **Data Retention:** 30 days standard, 1 year audit logs
- **Backup Recovery:** 4-hour RTO, 1-hour RPO

**Impact:** High — Customer trust  
**Files to Create:**
- `docs/SLA.md` (public-facing)
- `docs/operations/SLO-TRACKING.md` (internal)

---

### PROD-044: Network Segmentation

**Current State:** Single flat network. No firewall rules.

**Production Risk:** Lateral movement after breach, excessive blast radius.

**Required Changes:**
- Segment networks: Public (frontend), Private (backend, DB), Isolated (MCP)
- Configure firewall rules: Frontend → Backend (8000), Backend → DB (5432), Backend → Redis (6379)
- Block egress except allowlist: `*.googleapis.com`, `api.openai.com`, `api.anthropic.com`
- Enable VPC flow logs
- Test network isolation: Cannot reach DB from frontend

**Impact:** High — Defense in depth  
**Files to Create:**
- `docs/operations/NETWORK-ARCHITECTURE.md`
- `infrastructure/network-rules.tf` (if using Terraform)

---

### PROD-045: Container Security

**Current State:** Docker images built, but no security scanning or hardening.

**Production Risk:** Known vulnerabilities deployed, container escape attacks.

**Required Changes:**
- **Image Scanning:** Run Trivy in CI (`trivy image --severity CRITICAL,HIGH`)
- **Runtime Security:** Deploy Falco for anomaly detection (if Kubernetes)
- **Non-root User:** Run container as `USER 1000:1000` (not root)
- **Read-only Root:** Mount root filesystem read-only where possible
- **Minimal Base Image:** Use `python:3.12-slim` (not full Debian)
- **Secrets Not Baked In:** Inject secrets at runtime via env vars
- **CVE Monitoring:** Subscribe to security advisories for dependencies

**Impact:** High — Supply chain security  
**Files to Update:**
- `.github/workflows/docker-publish.yml` (add Trivy scan)
- `Dockerfile` (non-root user, slim base)
- `docs/SUPPLY-CHAIN-SECURITY.md`

---

### PROD-046: Backup Strategy ⚠️ **P0**

**Current State:** No automated backups. Data loss risk on infrastructure failure.

**Production Risk:** Catastrophic data loss, inability to recover from corruption.

**Required Changes:**
- **PostgreSQL Backups:** Daily full backup, hourly incremental (pg_dump or WAL archiving)
- **Redis Backups:** Daily snapshot (RDB) or AOF replication
- **Configuration Backups:** Vault secrets, `.env` files (encrypted), nginx config
- **Retention:** 30 days rolling, 1 year for audit compliance
- **Offsite Storage:** S3, Google Cloud Storage, or Azure Blob (encrypted)
- **Automated Restore Testing:** Weekly restore to staging, verify integrity
- **Backup Monitoring:** Alert if backup fails or is >25 hours old

**Impact:** Critical — Data durability  
**Files to Create:**
- `backend/scripts/backup_database.sh`
- `backend/scripts/restore_database.sh`
- `docs/operations/BACKUP-STRATEGY.md`

---

### PROD-047: Rollback Procedures ⚠️ **P0**

**Current State:** No rollback strategy. Failed deploys require manual fixes.

**Production Risk:** Extended downtime during bad deploys, inability to quickly revert.

**Required Changes:**
- **Blue-Green Deployment:** Maintain two environments, switch traffic instantly
- **Canary Rollout:** Deploy to 10% → 50% → 100% over 30 minutes
- **Instant Rollback:** Revert traffic to previous version in <60 seconds
- **Database Rollback:** Compatible schema changes only (additive), data migrations reversible
- **Automated Rollback Triggers:** P95 latency >15s, error rate >10%, health check fails
- **Testing Rollback:** Simulate failed deploy in staging weekly

**Impact:** Critical — Deployment safety  
**Files to Create:**
- `docs/operations/DEPLOYMENT-STRATEGY.md`
- `docs/operations/ROLLBACK-PROCEDURE.md`
- `.github/workflows/deploy-canary.yml`

---

### PROD-048: Session Management

**Current State:** JWT tokens, but no session tracking or revocation.

**Production Risk:** Stolen tokens remain valid, no way to force logout.

**Required Changes:**
- Implement session registry in Redis: `{session_id: {user_id, created_at, last_active}}`
- Session TTL: 24 hours, refresh on activity
- Refresh tokens: 30-day TTL, rotate on use
- Force logout: `/auth/logout` → invalidate session in Redis
- Revoke all sessions: `/auth/revoke-all` → delete all user sessions
- Session monitoring: Active sessions per user, alert on >10 concurrent

**Impact:** High — Security control  
**Files to Update:**
- `backend/api/v1/auth.py`
- `backend/security/session_manager.py`
- `docs/SECURITY.md`

---

### PROD-049: Staging Environment ⚠️ **P0**

**Current State:** No staging environment. Changes tested locally only.

**Production Risk:** Production bugs, untested migrations, integration failures.

**Required Changes:**
- Deploy staging environment: Identical to production (Docker, DB, Redis, MCP)
- Use anonymized production data (PII masked)
- Run full E2E test suite on every merge to `main`
- Test migrations on staging before production
- Test rollback procedures on staging
- Staging endpoint: `https://staging.dailybriefing.ai`
- Monitoring parity: Same Grafana/Prometheus setup

**Impact:** Critical — Quality gate  
**Files to Create:**
- `docker-compose.staging.yml`
- `docs/operations/STAGING-ENVIRONMENT.md`
- `.github/workflows/deploy-staging.yml`

---

### PROD-050: Smoke Tests ⚠️ **P0**

**Current State:** No post-deployment validation. Assumes deploy succeeded.

**Production Risk:** Silent failures, degraded service unnoticed.

**Required Changes:**
```python
# tests/smoke/test_production_smoke.py
async def test_health_check():
    """Verify /health returns 200."""
    response = await client.get("/health")
    assert response.status_code == 200

async def test_briefing_generation():
    """Verify critical path works."""
    response = await client.post("/v1/briefing", json={"user_id": "test"})
    assert response.status_code == 200
    assert "focus_plan" in response.json()

async def test_consent_flow():
    """Verify consent modal loads."""
    response = await client.get("/consent/google_calendar")
    assert response.status_code == 200
```

**Run After Every Deploy:**
- Execute smoke tests via GitHub Actions
- Block rollout if smoke tests fail
- Alert on-call if post-deploy smoke fails
- 5-minute timeout for smoke suite

**Impact:** Critical — Deployment safety  
**Files to Create:**
- `tests/smoke/test_production_smoke.py`
- `.github/workflows/smoke-tests.yml`

---

### PROD-051: Load Testing in CI

**Current State:** Load tests (if any) run manually.

**Production Risk:** Performance regressions undetected until production.

**Required Changes:**
- Add k6 load test to CI pipeline
- Run on every merge to `main` (before staging deploy)
- Test 10 concurrent users, 100 requests total
- Assert P95 latency <12s (buffer above 10s SLO)
- Assert error rate <1%
- Fail CI if performance regresses >20%

**Impact:** High — Performance quality gate  
**Files to Create:**
- `tests/load/k6-briefing.js`
- `.github/workflows/load-test.yml`

---

### PROD-052: Security Scanning (DAST)

**Current State:** SAST (static analysis) only. No dynamic security testing.

**Production Risk:** Runtime vulnerabilities, misconfigured auth, injection flaws.

**Required Changes:**
- **DAST:** Run OWASP ZAP against staging after deploy
- **Penetration Testing:** Annual third-party pentest
- **Vulnerability Disclosure:** `SECURITY.md` with responsible disclosure policy
- **Bug Bounty:** Consider HackerOne or Bugcrowd (post-launch)
- **Dependency Scanning:** Dependabot, `pip-audit` in CI (already exists)

**Impact:** High — Security assurance  
**Files to Create:**
- `.github/workflows/dast.yml`
- `SECURITY.md` (vulnerability disclosure)
- `docs/security/PENETRATION-TESTING.md`

---

### PROD-053: Chaos Engineering in Staging

**Current State:** No chaos testing. Resilience untested.

**Production Risk:** Unknown behavior during failures, cascading outages.

**Required Changes:**
- Test failure scenarios on staging:
  - Kill random container (simulate crash)
  - Inject 500ms network latency (simulate slow MCP)
  - Exhaust DB connections (simulate connection leak)
  - Corrupt Redis (simulate cache failure)
  - Rate-limit LLM API (simulate quota exhaustion)
- Run chaos tests weekly
- Document observed behavior and mitigations
- Game days: Simulate 5 simultaneous incidents

**Impact:** Medium — Resilience validation  
**Files to Create:**
- `tests/chaos/kill-container.sh`
- `tests/chaos/inject-latency.sh`
- `docs/operations/CHAOS-TESTING.md`

---

Follow the same pattern as `docs/gaps/WEEK1-IMPLEMENTATION-GUIDE.md` through `WEEK8`. Each production week gets: epic JSON ticket, implementation guide, kickoff prompt (PROD-KICKOFF-PROMPT.md for Week 1), proof package, learning doc.

### PROD Week 1: Security Hot Path (P0)

**Epic:** DB-E16 (to be created)  
**Branch:** `epic/prod-week1-security-hotpath`

| Day | Focus | PROD Gaps | Deliverables |
|---|---|---|---|
| 1 | Runtime spotlighting | PROD-002 | `spotlighting.py`, wire MCP + memory, tests |
| 2 | MCP response validator | PROD-003 | `mcp/validator.py`, allowlist, tests |
| 3 | Consensus production enablement | PROD-001, PROD-005 | Env updates, staging soak, latency proof |
| 4 | Deep health checks | PROD-032 | `/health/deep` endpoint, dependency checks |
| 5 | Database migration strategy | PROD-034 | Zero-downtime migration docs, rollback tests |

**Exit criteria:** All security P0 gaps closed; health checks operational; migration strategy tested.

---

### PROD Week 2: Infrastructure Foundations (P0)

**Epic:** DB-E17  
**Branch:** `epic/prod-week2-infra-foundations`

| Day | Focus | PROD Gaps | Deliverables |
|---|---|---|---|
| 1 | CORS + TLS configuration | PROD-036, PROD-037 | Production CORS allowlist, TLS 1.3 nginx config |
| 2 | Backup strategy | PROD-046 | Automated backups (DB, Redis, config), restore tests |
| 3 | Rollback procedures | PROD-047 | Blue-green deployment, canary rollout scripts |
| 4 | Staging environment | PROD-049 | Production-like staging, anonymized data |
| 5 | Smoke tests | PROD-050 | Post-deploy smoke test suite, CI integration |

**Exit criteria:** TLS operational; backups automated; staging environment deployed; smoke tests passing.

---

### PROD Week 3: Observability & Load Testing (P0/P1)

**Epic:** DB-E18  
**Branch:** `epic/prod-week3-observability-load`

| Day | Focus | PROD Gaps | Deliverables |
|---|---|---|---|
| 1 | Load testing suite | PROD-029 | k6 tests for 10/100/1K concurrent users |
| 2 | Deployment gates in CI | PROD-004 | ci.yml + docker-publish.yml jobs |
| 3 | Grafana dashboards | PROD-014–016 | Cache, dwell time, MITRE panels |
| 4 | Monitoring alerts | PROD-038 | Prometheus alerts, PagerDuty integration |
| 5 | Log aggregation | PROD-039 | Loki deployment, log shipping, retention |

**Exit criteria:** Load tested at scale; deployment gates enforced; alerting operational.

---

### PROD Week 4: Prompt v2 & Rate Limiting (P1)

**Epic:** DB-E19  
**Branch:** `epic/prod-week4-prompt-v2`

| Day | Focus | PROD Gaps | Deliverables |
|---|---|---|---|
| 1 | Task Agent v2 prompts | PROD-006 | 11-file structure, examples, tests |
| 2 | Calendar Agent v2 prompts | PROD-007 | 11-file structure, spotlighting in prompt |
| 3 | Orchestrator v2 prompts | PROD-008 | 11-file structure, synthesis examples |
| 4 | Prompt loader + input-security | PROD-009 | Load `input-security.md` in assembly |
| 5 | Production rate limiting | PROD-035 | Per-user/IP/agent rate limits |

**Exit criteria:** All 7 agents on v2 structure; rate limiting operational.

---

### PROD Week 5: Redis & Session Management (P1)

**Epic:** DB-E20  
**Branch:** `epic/prod-week5-redis-sessions`

| Day | Focus | PROD Gaps | Deliverables |
|---|---|---|---|
| 1 | Redis service + compose | PROD-013 | docker-compose, settings, health check |
| 2 | Working memory Redis TTL | PROD-013 | `memory/working.py` cache layer |
| 3 | Credential broker Redis cache | PROD-013 | `vault.py` multi-worker safe |
| 4 | Session management | PROD-048 | Session registry, refresh tokens, revocation |
| 5 | Load test + proof | PROD-013 | `proof/prod-week5/` |

**Exit criteria:** Redis operational; session management secure; cache metrics stable.

---

### PROD Week 6: Identity & Classifiers (P1)

**Epic:** DB-E21  
**Branch:** `epic/prod-week6-identity-classifiers`

| Day | Focus | PROD Gaps | Deliverables |
|---|---|---|---|
| 1 | NHI registry completion | PROD-011 | 7 agents in registry, updated tests |
| 2 | NHI runtime propagation | PROD-012 | Identity in envelope metadata at invoke |
| 3 | Constitutional classifiers expansion | PROD-010 | All agent I/O scanning |
| 4 | Agent OS kernel decision | PROD-018 | Extract module OR document distributed pattern |
| 5 | Integration tests + proof | PROD-010–012 | Security integration suite |

**Exit criteria:** 7-agent NHI; classifiers on all LLM paths; kernel documented.

---

### PROD Week 7: Operations & Hardening (P1)

**Epic:** DB-E22  
**Branch:** `epic/prod-week7-ops-hardening`

| Day | Focus | PROD Gaps | Deliverables |
|---|---|---|---|
| 1 | Production runbooks | PROD-031 | 8 incident response runbooks |
| 2 | Disaster recovery procedures | PROD-030 | DR plan, RTO/RPO targets, backup restoration |
| 3 | Secret rotation | PROD-033 | Automated rotation, expiry tracking |
| 4 | Network segmentation | PROD-044 | VPC isolation, firewall rules |
| 5 | Container security | PROD-045 | Trivy scanning, Falco, non-root user |

**Exit criteria:** Runbooks operational; DR tested; network hardened.

---

### PROD Week 8: Testing & SLAs (P1)

**Epic:** DB-E23  
**Branch:** `epic/prod-week8-testing-slas`

| Day | Focus | PROD Gaps | Deliverables |
|---|---|---|---|
| 1 | OpenSSF Scorecard CI | PROD-017 | CI job or documented waiver |
| 2 | Load testing in CI | PROD-051 | Automated load tests, performance regression checks |
| 3 | Security scanning (DAST) | PROD-052 | OWASP ZAP in CI, pentest scheduled |
| 4 | SLA/SLO documentation | PROD-043 | Formal SLAs (uptime, latency, support) |
| 5 | Production readiness review | All P0+P1 | Final checklist, go/no-go decision |

**Exit criteria:** All P0 + P1 gaps closed; security validated; SLAs documented.

---

### PROD Week 9: Documentation & Enterprise Extras (P2)

**Epic:** DB-E24  
**Branch:** `epic/prod-week9-docs-enterprise`

| Day | Focus | PROD Gaps | Deliverables |
|---|---|---|---|
| 1 | API documentation | PROD-040 | OpenAPI spec, Swagger UI |
| 2 | User documentation | PROD-041 | Setup, troubleshooting, FAQ, admin manual |
| 3 | Compliance documentation | PROD-042 | SOC 2 evidence (if applicable) |
| 4 | P2 enterprise features | PROD-019–028 | Delegation tokens, tool-chaining, MCP sandbox |
| 5 | Chaos engineering | PROD-053 | Chaos tests on staging, game day report |

**Exit criteria:** Documentation complete; P2 items implemented or deferred with risk acceptance.

---

## Files Requiring Updates

### New Files (Production Remediation)

| File | PROD Gap | Priority |
|---|---|---|
| **Security Layer** |
| `backend/security/spotlighting.py` | PROD-002 | P0 |
| `backend/mcp/validator.py` | PROD-003 | P0 |
| `backend/tests/security/test_spotlighting.py` | PROD-002 | P0 |
| `backend/tests/security/test_tool_poisoning.py` | PROD-003 | P0 |
| **Health & Testing** |
| `backend/api/v1/health.py` (deep health checks) | PROD-032 | P0 |
| `tests/smoke/test_production_smoke.py` | PROD-050 | P0 |
| `tests/load/k6-briefing.js` | PROD-029, PROD-051 | P0/P1 |
| `tests/chaos/kill-container.sh` | PROD-053 | P2 |
| **Infrastructure & Operations** |
| `backend/scripts/backup_database.sh` | PROD-046 | P0 |
| `backend/scripts/restore_database.sh` | PROD-046 | P0 |
| `infrastructure/nginx.conf` (TLS 1.3 config) | PROD-037 | P0 |
| `infrastructure/monitoring/prometheus-alerts.yml` | PROD-038 | P1 |
| `infrastructure/monitoring/loki-config.yml` | PROD-039 | P1 |
| `infrastructure/monitoring/grafana-production-dashboard.json` | PROD-014–016 | P1 |
| `docker-compose.staging.yml` | PROD-049 | P0 |
| **Security & Session Management** |
| `backend/security/secret_rotation.py` | PROD-033 | P1 |
| `backend/security/session_manager.py` | PROD-048 | P1 |
| `backend/middleware/rate_limit.py` | PROD-035 | P1 |
| **Operations Documentation** |
| `docs/operations/DISASTER-RECOVERY.md` | PROD-030 | P1 |
| `docs/operations/BACKUP-STRATEGY.md` | PROD-046 | P0 |
| `docs/operations/TLS-SETUP.md` | PROD-037 | P0 |
| `docs/operations/DEPLOYMENT-STRATEGY.md` | PROD-047 | P0 |
| `docs/operations/ROLLBACK-PROCEDURE.md` | PROD-047 | P0 |
| `docs/operations/STAGING-ENVIRONMENT.md` | PROD-049 | P0 |
| `docs/operations/DATABASE-MIGRATIONS.md` | PROD-034 | P0 |
| `docs/operations/HEALTH-CHECKS.md` | PROD-032 | P0 |
| `docs/operations/SECRET-ROTATION.md` | PROD-033 | P1 |
| `docs/operations/ALERTING.md` | PROD-038 | P1 |
| `docs/operations/LOG-AGGREGATION.md` | PROD-039 | P1 |
| `docs/operations/NETWORK-ARCHITECTURE.md` | PROD-044 | P1 |
| `docs/operations/ON-CALL.md` | PROD-038 | P1 |
| `docs/operations/CHAOS-TESTING.md` | PROD-053 | P2 |
| **Runbooks** (8 incident response guides) |
| `docs/operations/runbooks/MCP-TIMEOUT.md` | PROD-031 | P1 |
| `docs/operations/runbooks/LLM-API-DOWN.md` | PROD-031 | P1 |
| `docs/operations/runbooks/HIGH-LATENCY.md` | PROD-031 | P1 |
| `docs/operations/runbooks/DATABASE-CONNECTION-EXHAUSTED.md` | PROD-031 | P1 |
| `docs/operations/runbooks/REDIS-DOWN.md` | PROD-031 | P1 |
| `docs/operations/runbooks/CONSENSUS-FAILURE.md` | PROD-031 | P1 |
| `docs/operations/runbooks/DLQ-BACKLOG.md` | PROD-031 | P1 |
| `docs/operations/runbooks/SECURITY-ALERT.md` | PROD-031 | P1 |
| **User & Compliance Documentation** |
| `docs/user-guide/SETUP.md` | PROD-041 | P2 |
| `docs/user-guide/TROUBLESHOOTING.md` | PROD-041 | P2 |
| `docs/user-guide/FAQ.md` | PROD-041 | P2 |
| `docs/admin-guide/USER-MANAGEMENT.md` | PROD-041 | P2 |
| `docs/compliance/DATA-FLOWS.md` | PROD-042 | P2 |
| `docs/compliance/SECURITY-CONTROLS.md` | PROD-042 | P2 |
| `docs/SLA.md` | PROD-043 | P1 |
| `docs/API.md` (expanded) | PROD-040 | P2 |
| **Planning Documents** |
| `docs/gaps/production/PROD-PROPOSAL-REVIEW-SUMMARY.md` | — | Planning |
| `docs/gaps/production/PROD-KICKOFF-PROMPT.md` | — | Planning |
| `docs/gaps/production/PROD-WEEK1-IMPLEMENTATION-GUIDE.md` | Week 1 | P0 |
| `docs/gaps/production/PROD-WEEK2-IMPLEMENTATION-GUIDE.md` through WEEK9 | Weeks 2-9 | P0-P2 |
| **Kernel (Optional)** |
| `backend/kernel/__init__.py` | PROD-018 | P1 |

### Existing Files to Update

| File | PROD Gap | Priority |
|---|---|---|
| `.env.production.example` | PROD-001, PROD-005 | P0 |
| `.github/workflows/ci.yml` | PROD-004, PROD-017 | P0/P1 |
| `.github/workflows/docker-publish.yml` | PROD-004 | P0 |
| `backend/agents/focus/node.py` | PROD-002 | P0 |
| `backend/agents/task/node.py` | PROD-002 | P0 |
| `backend/agents/calendar/node.py` | PROD-002 | P0 |
| `backend/mcp/client.py` | PROD-003 | P0 |
| `backend/prompts_loader.py` | PROD-009 | P1 |
| `backend/security/nhi_registry.json` | PROD-011 | P1 |
| `prompts/task/*`, `prompts/calendar/*`, `prompts/orchestrator/*` | PROD-006–008 | P1 |
| `docker-compose.yml` | PROD-013 | P1 |
| `docs/SECURITY.md`, `docs/MCP.md`, `docs/DEPLOYMENT-GATES.md` | Multiple | P0–P1 |
| `AGENT.md` | Production MVP section | P1 |

---

## Testing Requirements

### New Test Suites (Production)

| Test File | PROD Gap | Coverage |
|---|---|---|
| `backend/tests/security/test_spotlighting.py` | PROD-002 | Injection corpus, marker presence |
| `backend/tests/security/test_tool_poisoning.py` | PROD-003 | Schema reject, anomaly detection |
| `backend/tests/production/test_consensus_production.py` | PROD-001 | Consensus on, E2E latency |
| `backend/tests/observability/test_deployment_gates_ci.py` | PROD-004 | Gate failure blocks |
| `backend/tests/prompts/test_v2_migration.py` | PROD-006–008 | All agents v2 structure |
| `backend/tests/security/test_constitutional_full_coverage.py` | PROD-010 | All agent I/O paths |
| `backend/tests/infrastructure/test_redis_memory.py` | PROD-013 | TTL, multi-worker |

### Verification Gate (unchanged)

```bash
uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest
```

### Production Pre-Launch Checklist

```bash
# 1. Full test suite
uv run pytest

# 2. Deployment gates (production mode)
APP_ENV=production uv run python -c "
from backend.observability.deployment_gates import check_deployment_gates
r = check_deployment_gates()
assert r.all_pass, r
print('All gates passed')
"

# 3. AI-BOM validation
uv run pytest backend/tests/security/test_ai_bom.py -v

# 4. Security path smoke (spotlighting + validator — after PROD Week 1)
uv run pytest backend/tests/security/test_spotlighting.py backend/tests/security/test_tool_poisoning.py -v

# 5. Consensus E2E (staging with real keys)
ENABLE_CONSENSUS_WORKFLOW=true uv run pytest backend/tests/architecture/test_consensus.py -v
```

---

## Epic Ticket Creation Workflow

**Pattern:** Same as `docs/gaps/KICKOFF-PROMPT.md` and Weeks 1–8.

| Production Week | Epic JSON (to create) | Guide (to create) | Kickoff |
|---|---|---|---|
| PROD Week 1 | `DB-E16-production-week1.json` | `PROD-WEEK1-IMPLEMENTATION-GUIDE.md` | `PROD-KICKOFF-PROMPT.md` |
| PROD Week 2 | `DB-E17-production-week2.json` | `PROD-WEEK2-IMPLEMENTATION-GUIDE.md` | `PROD-WEEK2-KICKOFF-PROMPT.md` |
| PROD Week 3 | `DB-E18-production-week3.json` | `PROD-WEEK3-IMPLEMENTATION-GUIDE.md` | `PROD-WEEK3-KICKOFF-PROMPT.md` |
| PROD Week 4 | `DB-E19-production-week4.json` | `PROD-WEEK4-IMPLEMENTATION-GUIDE.md` | `PROD-WEEK4-KICKOFF-PROMPT.md` |
| PROD Week 5 | `DB-E20-production-week5.json` | `PROD-WEEK5-IMPLEMENTATION-GUIDE.md` | `PROD-WEEK5-KICKOFF-PROMPT.md` |
| PROD Week 6 | `DB-E21-production-week6.json` | `PROD-WEEK6-IMPLEMENTATION-GUIDE.md` | `PROD-WEEK6-KICKOFF-PROMPT.md` |
| PROD Week 7 | `DB-E22-production-week7.json` | `PROD-WEEK7-IMPLEMENTATION-GUIDE.md` | `PROD-WEEK7-KICKOFF-PROMPT.md` |
| PROD Week 8 | `DB-E23-production-week8.json` | `PROD-WEEK8-IMPLEMENTATION-GUIDE.md` | `PROD-WEEK8-KICKOFF-PROMPT.md` |
| PROD Week 9 | `DB-E24-production-week9.json` | `PROD-WEEK9-IMPLEMENTATION-GUIDE.md` | `PROD-WEEK9-KICKOFF-PROMPT.md` |

**Ticket format:** DB-E2 `Description` shape — `IMPLEMENTATION DETAILS`, `EFFORT`, `PROJECT AREA`, `DEPENDENCIES`, `TESTING CRITERIA`, `EDGE CASES`. Canonical reference: `docs/jira-tickets-json/DB-E15-gap-remediation-week8.json`.

**Integration branch:** `epic/autonomus-implementation` (or successor production integration branch).

---

## Recommendations

### Immediate Actions (Before PROD Week 1)

1. **Create** `PROD-PROPOSAL-REVIEW-SUMMARY.md` — executive summary for stakeholders
2. **Create** `PROD-KICKOFF-PROMPT.md` — Week 1 agent kickoff (mirror `docs/gaps/KICKOFF-PROMPT.md`)
3. **Create** `DB-E16-production-week1.json` — epic ticket with 5 daily tasks
4. **Update** `docs/PLAN.md` — add Production Remediation section (PROD Weeks 1–6)
5. **Archive** stale `docs/tasks/checkpoint.md` or refresh for production kickoff

### Production Launch Decision Matrix

| Scenario | Minimum Required | Timeline | Risk |
|---|---|---|---|
| **Internal demo / staging** | Current codebase | ✅ Ready today | Low (no external users) |
| **Staging deployment** | P0 infrastructure (Weeks 1-3) | **3 weeks** | Medium (isolated, monitored) |
| **Limited production (10 trusted users)** | P0 complete (Weeks 1-3) | **3 weeks** | Medium-High (limited blast radius) |
| **Beta production (100 users)** | P0 + P1 critical (Weeks 1-6) | **6 weeks** | Medium (monitored, rollback ready) |
| **Scaled production (1,000+ users)** | P0 + P1 complete (Weeks 1-8) | **8 weeks** | Low (hardened infrastructure) |
| **Enterprise / regulated** | All gaps (Weeks 1-9) | **9 weeks** | Very Low (fully compliant) |

### Risk Acceptance for Deferred P2

If launching after P0+P1 only, document accepted risks for:
- No X.509 NHI (PROD-024) — JSON registry sufficient for single-tenant
- No hardware-backed Vault (PROD-023) — dev broker with encrypted refresh tokens
- No MCP sandbox CPU caps (PROD-021) — rely on timeout + validator
- Manual OpenSSF review (PROD-017) — if CI automation deferred

---

## Conclusion

Gap remediation Weeks 1–8 delivered a **substantially complete** platform: 436 tests, full agent graph, memory architecture, consent, DLQ, caching, supply-chain manifest, and Cosign signing. The codebase is **demo-ready and staging-ready today**.

For **production deployment per v2.0.0**, **53 production-specific gaps** remain:

**P0 (14 gaps) — Block launch:**
1. Consensus workflow disabled in production config (PROD-001)
2. No runtime spotlighting (PROD-002)
3. No MCP validator layer (PROD-003)
4. Deployment gates not in CI (PROD-004)
5. Production env misaligned (PROD-005)
6. Load testing not completed (PROD-029)
7. Deep health checks missing (PROD-032)
8. Database migration strategy undefined (PROD-034)
9. CORS configuration incomplete (PROD-036)
10. TLS/SSL not configured (PROD-037)
11. No staging environment (PROD-049)
12. No smoke tests (PROD-050)
13. Backup strategy missing (PROD-046)
14. Rollback procedures undefined (PROD-047)

**P1 (24 gaps) — Block scale:**
Code-level: Prompt v2 completion, full classifier coverage, NHI completion, Redis, Agent OS kernel  
Operations: DR procedures, production runbooks, secret rotation, monitoring alerts, log aggregation, network segmentation, container security, session management, load testing in CI, security scanning (DAST), SLA/SLO documentation

**P2 (15 gaps) — Enterprise extras:**
Code: Delegation tokens, tool-chaining limits, MCP sandbox, config signing, Vault production, X.509 NHI, chaos CI  
Documentation: API docs, user docs, compliance docs, chaos engineering

**Estimated timeline:** 9 production weeks (PROD Week 1–9) to close P0 + P1 + P2.

**Recommended Milestones:**
- **Week 3:** Staging deployment (P0 infrastructure complete)
- **Week 6:** Limited production (P0 + critical P1 complete)
- **Week 8:** Scaled production (All P1 complete)
- **Week 9:** Enterprise-ready (P2 complete or deferred with risk acceptance)

**Critical Insight:** The original 28 gaps were **code-focused** (security architecture, testing). The additional 25 operational gaps cover **production infrastructure** (backups, TLS, staging, runbooks, monitoring), which are equally critical for safe launch. Both must be addressed.

**Next documents:** `PROD-PROPOSAL-REVIEW-SUMMARY.md` → `PROD-KICKOFF-PROMPT.md` → weekly implementation guides and epic JSON tickets.

---

## Appendix: Original Gap → Production Gap Mapping

| Original Gap # | Original Status (June 6) | Production Gap | Current Status (June 7) |
|---|---|---|---|
| #1–7 | 🔴 | PROD-001 | 🟡 Built, not enabled |
| #114 | 🔴 | PROD-002 | 🔴 Runtime missing |
| #117 | 🔴 | PROD-003, PROD-020 | 🔴 Validator missing |
| #59 | 🔴 | PROD-004 | 🟡 Code only |
| #136 | 🟡 | PROD-006–009 | 🟡 4/7 agents |
| #126 | 🔴 | PROD-010 | 🟡 Critic only |
| #92–93 | 🔴 | PROD-011–012, PROD-024 | 🟡 JSON, 5 agents |
| #8, #19 | 🔴 | PROD-013 | 🔴 No Redis |
| #134, #129 | 🔴 | PROD-014–016 | 🟡 Metrics only |
| #116 | 🔴 | PROD-017 | 🟡 Manual |
| #27–29 | 🔴 | PROD-018, PROD-021 | 🟡 Distributed |
| #118 | 🔴 | PROD-019 | 🟡 Partial |
| #86 | 🔴 | PROD-022 | 🔴 Not started |
| #124–125 | 🔴 | PROD-024–025 | 🔴 Not started |

---

*Production Gap Analysis Review — Created June 7, 2026 | Updated June 8, 2026 (Operational readiness gaps added)*
