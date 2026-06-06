# Gap Analysis Review — IBM + Claude Zero-Trust Comprehensive Analysis

**Date:** June 4-6, 2026  
**Proposal:** `007-01-ai-daily-briefing-assistant5.md` v1.5.0  
**Guidance Sources:**
- `docs/example-code/examples/2026-12-01-youtube-IBM.md` (IBM Multi-Agent AI)
- `docs/example-code/examples/2026-12-01-zero-trust-ai-agents-summary.md` (Claude/Anthropic Zero-Trust)
**Alignment Analysis:** `docs/gaps/CLAUDE-ZERO-TRUST-ALIGNMENT.md`

---

## Executive Summary

This document reviews the AI Daily Briefing Assistant proposal against **IBM's multi-agent AI best practices** and **Claude/Anthropic's Zero-Trust framework for AI agents**, identifying **121 total gaps** requiring remediation before production deployment.

**Update (June 6, 2026):** Added 22 new gaps (#114-#135) from Claude Zero-Trust analysis, covering critical supply chain, memory protection, and advanced threat defenses not captured in the original IBM-based review.

**Status Overview:**
- ✅ **Already Implemented:** 23 gaps (19%)
- 🟡 **Partially Implemented:** 31 gaps (26%)  
- 🔴 **Not Implemented:** 67 gaps (55%)

**Critical Priorities:**
- **P0 (Critical):** 24 gaps — Immediate action required (was 18, added 6 from Claude)
- **P1 (High):** 52 gaps — Required before production (was 39, added 13 from Claude)
- **P2 (Medium):** 38 gaps — Enhancement and optimization (was 35, added 3 from Claude)
- **P3 (Low):** 7 gaps — Nice-to-have

---

## Critical Gaps Requiring Immediate Action

### 1. Multi-Agent Verification Architecture (Gaps #1-7)

**Current State:** The proposal includes Task, Calendar, Focus, and Critic agents, but lacks the verification-consensus-adversarial pattern recommended by IBM.

**Required Changes:**
- Add dedicated **Verification Agent** (distinct from Critic's safety role)
- Add **Adversarial/Red Team Agent** to runtime graph
- Implement **Generator → Verification → Adversarial → Consensus** workflow
- Add escalation path for agent disagreement (beyond security violations)
- Document consensus evaluation criteria

**Impact:** High — Core architectural pattern for reliability
**Files to Update:**
- `docs/ARCHITECTURE.md`
- `backend/agents/AGENT.md`
- `backend/graph/builder.py`
- Add `backend/agents/verification/` and `backend/agents/adversarial/`

---

### 2. Four-Layer Memory Architecture (Gaps #8-13)

**Current State:** Implicit memory in LangGraph state and prompts, but no formal CoALA-compliant memory architecture.

**Required Changes:**
- Formalize **Working Memory** (context window management)
- Specify **Semantic Memory** (persistent facts, policies, RAG)
- Implement **Procedural Memory** (skill library with progressive disclosure)
- Implement **Episodic Memory** (distilled lessons, not raw logs)
- Map memory requirements per agent

**Impact:** High — Scalability and learning capability
**Files to Update:**
- Create `docs/MEMORY-ARCHITECTURE.md`
- Create `backend/memory/` module
- Update `backend/AGENT.md`

---

### 3. Last-Mile Identity & Credential Management (Gaps #18-22)

**Current State:** `.env` secrets, no JIT credentials, no ABAC/PBAC

**Required Changes:**
- Implement **credential broker/vault** for JIT short-lived credentials
- Propagate user identity + intent + delegation through full chain
- Add **ABAC/PBAC** enforcement at data access time
- Add telemetry-driven permission tightening

**Impact:** Critical — Security and compliance
**Files to Update:**
- Create `backend/security/vault.py`
- Update `backend/mcp/client.py`
- Update `docs/SECURITY.md`
- Create `docs/IDENTITY-PROPAGATION.md`

---

### 4. Agent OS Kernel Components (Gaps #27-29)

**Current State:** LangGraph orchestration only, no formal Agent OS layer

**Required Changes:**
- Document **Agent OS kernel** components:
  - Scheduler (task prioritization)
  - Memory Manager
  - Tool Manager (sandboxed execution)
  - Identity Manager
  - Guardrails
- Implement sandboxed tool execution for MCP

**Impact:** Medium — Production reliability
**Files to Update:**
- Create `docs/AGENT-OS.md`
- Update `backend/graph/builder.py`

---

### 5. Rogue Agent Drift Detection (Gap #99)

**Current State:** No drift detection in observability

**Required Changes:**
- Add **guardrail violation trend** as tier-1 SLO
- Alert when violation rate >2× over 7 days
- Tie to red-team cadence

**Impact:** High — Runtime security
**Files to Update:**
- `docs/OBSERVABILITY.md` ✅ (being updated now)
- `backend/schemas/envelope.py` (add violation tracking)

---

## Detailed Gap Tracking

### Architecture & Design Principles (Gaps #1-17)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 1 | Add Verification Agent (fact-checking) | 🔴 Not Implemented | P0 |
| 2 | Add Adversarial/Red Team Agent | 🔴 Not Implemented | P0 |
| 3 | Implement Generator→Verification→Adversarial workflow | 🔴 Not Implemented | P0 |
| 4 | Implement consensus-based trust model | 🔴 Not Implemented | P0 |
| 5 | Add human escalation on disagreement | 🔴 Not Implemented | P0 |
| 6 | Apply "verification over confidence" principle | 🟡 Partial (Critic only) | P0 |
| 7 | Require independent validation | 🔴 Not Implemented | P0 |
| 8 | Formalize four memory types (CoALA) | 🔴 Not Implemented | P1 |
| 9 | Specify Working Memory scope | 🟡 Implicit in LangGraph | P1 |
| 10 | Specify Semantic Memory | 🟡 Prompts + docs only | P1 |
| 11 | Implement Procedural Memory (skills) | 🔴 Not Implemented | P1 |
| 12 | Implement Episodic Memory (distilled lessons) | 🔴 Not Implemented | P1 |
| 13 | Map memory layers per agent | 🔴 Not Implemented | P1 |
| 14 | Add CAG vs Long Context decision criteria | 🔴 Not Implemented | P2 |
| 15 | Plan prompt caching / KV reuse | 🔴 Not Implemented | P2 |
| 16 | Mitigate "lost in the middle" | 🔴 Not Implemented | P2 |
| 17 | State explicitly as orchestration layer atop systems of record | ✅ Implemented | — |

### Security & Identity (Gaps #18-30)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 18 | Last-mile identity propagation | 🔴 Not Implemented | P0 |
| 19 | Credential broker/vault for JIT credentials | 🔴 Not Implemented | P0 |
| 20 | ABAC/PBAC at data access time | 🔴 Not Implemented | P0 |
| 21 | Telemetry-driven permission tightening | 🔴 Not Implemented | P1 |
| 22 | Define max steps/retries/runtime | 🟡 Token budgets only | P0 |
| 23 | Track progress across retries | 🔴 Not Implemented | P1 |
| 24 | Add plan validation step | 🟡 Critic reviews, not validates | P0 |
| 25 | Require clarification when uncertain | 🔴 Not Implemented | P1 |
| 26 | Tier tools as read/write/delete | 🟡 MCP scopes exist | P1 |
| 27 | Document Agent OS kernel | 🔴 Not Implemented | P1 |
| 28 | Define task prioritization | 🔴 Not Implemented | P2 |
| 29 | Require sandboxed tool execution | 🔴 Not Implemented | P0 |
| 30 | Define risk-based automation thresholds | 🔴 Not Implemented | P1 |

### Consent & Governance (Gaps #31-40)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 31 | Expand Agentic Consent to full dynamic governance | 🟡 Partial (basic consent) | P1 |
| 32 | Add JIT human consent for sensitive actions | 🟡 Consent exists, not JIT prompting | P1 |
| 33 | Evolve to Agentic RAG (dynamic retrieval) | 🔴 Not Implemented | P2 |
| 34 | Add source validation & cross-referencing | 🔴 Not Implemented | P1 |
| 35 | Document CLI vs MCP selection rules | 🟡 Mentioned in MCP.md | P2 |
| 36 | Include synthetic monitoring | 🔴 Not Implemented | P1 |
| 37 | Apply context engineering pillars | 🔴 Not Implemented | P1 |
| 38 | Enforce precision retrieval | 🔴 Not Implemented | P1 |
| 39 | Evaluate hybrid/GraphRAG | 🔴 Not Implemented | P2 |
| 40 | Add context compression | 🔴 Not Implemented | P2 |

### Agent Roles & Orchestration (Gaps #41-50)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 41 | Document Build/Reuse/Hybrid orchestration | 🔴 Not Implemented | P2 |
| 42 | Add runtime Learner Agent | 🔴 Not Implemented | P1 |
| 43 | Justify Orchestrator as Supervisor+Presenter | ✅ Documented | — |
| 44 | Define per-role model selection | 🔴 Not Implemented | P2 |
| 45 | State ADK + RAG hybrid | 🔴 Not Implemented | P2 |
| 46 | Adopt Agent Skills standard | 🔴 Not Implemented | P2 |
| 47 | Embed seven agent-engineering disciplines | 🟡 Partial in docs | P1 |
| 48 | Elevate strict tool I/O schemas | ✅ Pydantic schemas | — |
| 49 | Implement IAM maturity ≥ Foundation | 🔴 Not Implemented | P0 |
| 50 | Use ephemeral JIT credentials | 🔴 Not Implemented | P0 |

### Observability & Operations (Gaps #51-70)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 51 | Maintain delegation audit chain | 🔴 Not Implemented | P0 |
| 52 | Enforce last-hop real-time authorization | 🔴 Not Implemented | P0 |
| 53 | Address AI technical debt | 🟡 Partial | P1 |
| 54 | Place AI gateway | 🔴 Not Implemented | P2 |
| 55 | Integrate code risk intelligence | 🔴 Not Implemented | P2 |
| 56 | Apply agentic trust controls | 🔴 Not Implemented | P0 |
| 57 | Authenticate inter-agent communication | ✅ In-process, N/A | — |
| 58 | Implement AgentOps metrics | 🟡 Basic metrics exist | P1 |
| 59 | Define deployment gates on metrics | 🔴 Not Implemented | P1 |
| 60 | Add optimization loop | 🔴 Not Implemented | P2 |
| 61 | Specify five context layers | 🔴 Not Implemented | P1 |
| 62 | Map to OWASP Agent Top 10 | 🟡 LLM Top 10 only | P1 |
| 63 | Treat memory/RAG as untrusted | 🟡 Input sanitization only | P1 |
| 64 | Sandbox agent-generated code | 🔴 Not Implemented | P0 |
| 65 | Add agentic runtime security | 🔴 Not Implemented | P0 |
| 66 | Implement full HITL layers | 🟡 Consent only | P1 |
| 67 | Expose reasoning/trace observability | 🟡 Trace IDs only | P1 |
| 68 | Document override & rollback | 🔴 Not Implemented | P1 |
| 69 | Capture reasoning-level feedback | 🔴 Not Implemented | P2 |
| 70 | Classify agents on capability×risk matrix | 🔴 Not Implemented | P1 |

### System Design & Architecture (Gaps #71-99)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 71 | Avoid super-agent expansion | ✅ Implemented | — |
| 72 | Plan hierarchical decomposition | 🔴 Not Implemented | P2 |
| 73 | Validate plans at each tier | 🟡 Critic only | P1 |
| 74 | Document RAG vs long context decision | 🔴 Not Implemented | P2 |
| 75 | Define agentic storage policy | 🔴 Not Implemented | P2 |
| 76 | Adopt Spec-Driven Development | 🟡 For autonomous epics | P2 |
| 77 | Align with 2026 threat intelligence | 🟡 OWASP GenAI covered | P1 |
| 78 | Specify quantization/inference strategy | 🟡 LOCAL_LLM.md exists | P2 |
| 79 | Declare multimodal scope | 🔴 Not Implemented | P3 |
| 80 | Declare predictive + generative scope | 🔴 Not Implemented | P3 |
| 81 | Manage MCP schema token budget | 🔴 Not Implemented | P2 |
| 82 | Map LangGraph to ReAct | 🟡 Implicit | P2 |
| 83 | Treat disagreement as valuable signal | 🔴 Not Implemented | P1 |
| 84 | Require explainability & auditability | 🟡 Trace IDs only | P1 |
| 85 | Add risk-proportional architecture justification | 🔴 Not Implemented | P2 |
| 86 | Assign organizational governance | 🔴 Not Implemented | P1 |
| 87 | Extend reliability engineering | 🟡 Circuit breakers exist | P1 |
| 88 | Position red teaming as ongoing | 🔴 Not Implemented | P1 |
| 89 | Route security violations consistently | ✅ Implemented | — |
| 90 | Document fine-tuning as out of scope | ✅ Implicit | — |
| 91 | Quantization as default local inference | 🟡 Documented, not enforced | P2 |
| 92 | Add NHI posture-management observability | 🔴 Not Implemented | P0 |
| 93 | Add five-imperative NHI definition-of-done | 🔴 Not Implemented | P0 |
| 94 | Require third-party SaaS/MCP security assessments | 🔴 Not Implemented | P0 |
| 95 | Declare human-on-the-loop as default | 🔴 Not Implemented | P1 |
| 96 | Add confidence-threshold routing | 🔴 Not Implemented | P1 |
| 97 | Add handoff contract integrity validation | 🔴 Not Implemented | P1 |
| 98 | Mitigate OWASP Agent #9 (trust exploitation) | 🔴 Not Implemented | P1 |
| 99 | Add rogue agent drift detection | 🔴 Not Implemented | P0 |

---

## Claude Zero-Trust Specific Gaps (Gaps #114-#135)

**Source:** `docs/example-code/examples/2026-12-01-zero-trust-ai-agents-summary.md`  
**Analysis:** `docs/gaps/CLAUDE-ZERO-TRUST-ALIGNMENT.md`

These 22 gaps were identified from Claude/Anthropic's Zero-Trust framework and represent critical security concerns not covered in the IBM-based analysis.

### Supply Chain Security (Gaps #114-#116, #127)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 114 | **Spotlighting for indirect injection** (calendar/email data) | 🔴 Not Implemented | P0 |
| 115 | AI-BOM for model provenance (OWASP AI-BOM) | 🔴 Not Implemented | P1 |
| 116 | OpenSSF Scorecard in CI pipeline | 🔴 Not Implemented | P1 |
| 127 | Vendor security assessments (include FOSS) | 🔴 Not Implemented | P1 |

### Identity & Credential Security (Gaps #117-#119, #128)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 117 | **Tool poisoning & rug-pull defense** (MCP validation) | 🔴 Not Implemented | P0 |
| 118 | **Confused deputy attack prevention** (delegation framework) | 🔴 Not Implemented | P0 |
| 119 | Memory-based privilege retention prevention | 🔴 Not Implemented | P1 |
| 128 | Per-action authorization with real-time policy evaluation | 🔴 Not Implemented | P1 |

### Memory Protection & Integrity (Gaps #120-#122, #132)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 120 | **RAG poisoning defense** (if using RAG) | 🔴 Not Implemented | P0* |
| 121 | Shared context poisoning (if multi-user) | 🔴 Not Implemented | P2 |
| 122 | Long-term behavioral drift detection | 🔴 Not Implemented | P1 |
| 132 | Memory quarantine workflow for suspected poisoning | 🔴 Not Implemented | P1 |

### Observability & Detection (Gaps #123, #129, #134-#135)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 123 | Cryptographically sealed audit logs (immutable) | 🔴 Not Implemented | P1 |
| 129 | MITRE ATT&CK detection coverage mapping | 🔴 Not Implemented | P1 |
| 134 | Dwell time SLO (<1hr anomaly→awareness) | 🔴 Not Implemented | P1 |
| 135 | Alert investigation coverage tracking (95%+) | 🔴 Not Implemented | P1 |

### Advanced Defenses (Gaps #126, #133)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 126 | Constitutional classifiers (95% jailbreak block) | 🔴 Not Implemented | P1 |
| 133 | Blast radius quantification per agent | 🔴 Not Implemented | P1 |

### Governance & Operations (Gaps #130-#131)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 130 | Multi-incident chaos testing (5 simultaneous) | 🔴 Not Implemented | P1 |
| 131 | Emergency change authorization procedures | 🔴 Not Implemented | P1 |

### Advanced Tier (Future/Regulated) (Gaps #124-#125)

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 124 | Hardware-backed identity (HSM/TPM) | 🔴 Not Implemented | P2 (P0 if regulated) |
| 125 | Confidential computing readiness (AMD SEV/Intel TDX) | 🔴 Not Implemented | P2 (P0 if regulated) |

**Notes:**
- Gap #120 is P0 only if using RAG for documentation/policies
- Gaps #124-#125 are P2 for general use, P0 for regulated industries

---

## Prompt Engineering & LLM Best Practices (Gap #136)

**Source:** Claude Prompting Best Practices + OpenAI GPT-5.5 Prompt Guidance  
**Analysis Date:** 2026-06-06

| Gap # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 136 | **Prompt engineering standards** (Claude + OpenAI best practices) | 🟡 Partial → ✅ (Focus v2) | P0 |

### Current State (Before Remediation)
- **Minimal prompts:** 3-9 lines per agent (vague instructions)
- **No examples:** Zero-shot prompting only (no few-shot)
- **No security:** Generic guardrails, no spotlighting
- **No validation:** No quality self-checks or output schemas
- **No reasoning:** No thinking guidance for complex decisions

### Required Changes (Claude + OpenAI Guidance)
1. **Clear, explicit instructions** — No vague language
2. **3-5 examples per agent** — Few-shot prompting for consistency
3. **XML structure** — Organize complex prompts unambiguously
4. **Context and motivation** — Explain why quality matters
5. **Explicit output schemas** — JSON validation with constraints
6. **Reasoning guidance** — Thinking patterns for complex tasks
7. **Tool use instructions** — Explicit triggers and anti-patterns
8. **Edge case handling** — Empty inputs, errors, failures
9. **Quality self-check** — 10-15 point validation checklist
10. **Security (spotlighting)** — Microsoft technique for external data
11. **Communication style** — Tone, voice, tense, perspective
12. **Model configuration** — Effort, temperature, thinking settings

### Implementation Status
- ✅ **Focus Agent:** Complete v2.0.0 rewrite (reference implementation)
  - 500+ line system prompt (was 3 lines)
  - 5 complete examples (was 0)
  - Spotlighting for external data
  - 15-point quality checklist
  - Comprehensive security (5 defense layers)
- 🔴 **Task Agent:** Not started
- 🔴 **Calendar Agent:** Not started
- 🔴 **Critic Agent:** Not started
- 🔴 **Orchestrator Agent:** Not started
- 🔴 **Security Agent:** Not started

### Files Created
- `prompts/focus/system.md` — Comprehensive system prompt (v2.0.0)
- `prompts/focus/examples.md` — 5 complete examples with reasoning
- `prompts/focus/input-security.md` — Security defenses (spotlighting, validation)
- `prompts/focus/CHANGELOG.md` — Version history and migration notes
- `docs/PROMPT-ENGINEERING-GUIDE.md` — Standards for all agents

### Success Criteria
- [ ] All agents upgraded to v2.0.0 prompt structure
- [ ] 3-5 examples per agent
- [ ] Spotlighting implemented for all external data
- [ ] Quality self-check in all prompts
- [ ] Security testing for all agents (>95% jailbreak block rate)
- [ ] Accuracy >90% on evaluation sets
- [ ] Token efficiency improvement >10%

### References
- **Claude Best Practices:** https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- **OpenAI Best Practices:** https://developers.openai.com/api/docs/guides/prompt-guidance?model=gpt-5.5
- **Guide:** `docs/PROMPT-ENGINEERING-GUIDE.md`
- **Reference Implementation:** `prompts/focus/` (v2.0.0)

---

## Remediation Roadmap

### Phase 1: Critical Security & Architecture (Weeks 1-3)

**Original Gaps:**
- [ ] Gap #1-7: Multi-agent verification architecture
- [ ] Gap #18-20: Last-mile identity & JIT credentials
- [ ] Gap #49-50: IAM maturity baseline
- [ ] Gap #92-94: NHI observability & assessment
- [ ] Gap #99: Rogue agent drift detection

**NEW from Claude:**
- [ ] **Gap #114: Spotlighting** (Week 2-3) — Calendar/email indirect injection defense
- [ ] **Gap #117: Tool Poisoning** (Week 2-3) — MCP tool validation layer
- [ ] **Gap #118: Confused Deputy** (Week 3-4) — Delegation framework
- [ ] **Gap #133: Blast Radius** (Week 2-3) — Risk quantification per agent

### Phase 2: Memory & Observability (Weeks 4-5)

**Original Gaps:**
- [ ] Gap #8-13: Four-layer memory architecture
- [ ] Gap #58-61: AgentOps metrics & context layers
- [ ] Gap #62-65: OWASP Agent Top 10 compliance
- [ ] Gap #87-88: Reliability engineering & red teaming

**NEW from Claude:**
- [ ] **Gap #119: Memory-Based Privilege Retention** (Week 4-5) — Prevent privilege escalation via memory
- [ ] **Gap #120: RAG Poisoning** (Week 4-5) — If using RAG for docs/policies
- [ ] **Gap #128: Per-Action Authorization** (Week 3-4) — Real-time policy evaluation
- [ ] **Gap #132: Memory Quarantine** (Week 4-5) — Poisoned memory containment

### Phase 3: Supply Chain & Advanced Defenses (Weeks 5-6)

**Original Gaps:**
- [ ] Gap #62-65: OWASP Agent Top 10 compliance (continued)
- [ ] Gap #87-88: Reliability engineering & red teaming

**NEW from Claude:**
- [ ] **Gap #115: AI-BOM** (Week 5-6) — Model provenance tracking
- [ ] **Gap #116: OpenSSF Scorecard** (Week 5-6) — Dependency health in CI
- [ ] **Gap #123: Cryptographic Log Sealing** (Week 5-6) — Immutable audit logs
- [ ] **Gap #127: Vendor Assessments (FOSS)** (Week 5-6) — Include open-source dependencies

### Phase 4: Governance & Operations (Weeks 6-7)

**Original Gaps:**
- [ ] Gap #31-32: Dynamic consent & JIT prompting
- [ ] Gap #66-69: Full HITL layers & reasoning observability
- [ ] Gap #86: Organizational governance
- [ ] Gap #95-98: Human-on-the-loop & trust controls

**NEW from Claude:**
- [ ] **Gap #126: Constitutional Classifiers** (Week 6-7) — 95% jailbreak block rate
- [ ] **Gap #122: Long-Term Drift** (Week 6-7) — Extends #99 for gradual degradation
- [ ] **Gap #129: MITRE ATT&CK** (Week 6-7) — Detection coverage mapping
- [ ] **Gap #134: Dwell Time SLO** (Week 6-7) — <1hr anomaly→awareness target
- [ ] **Gap #135: Alert Coverage** (Week 6-7) — Track % of alerts investigated

### Phase 5: Governance Hardening (Weeks 7-8)

**Original Gaps:**
- [ ] Gap #31-32: Dynamic consent (continued)
- [ ] Gap #66-69: Full HITL layers (continued)
- [ ] Gap #86: Organizational governance (continued)

**NEW from Claude:**
- [ ] **Gap #130: Multi-Incident Chaos Testing** (Week 7-8) — 5 simultaneous incidents tabletop
- [ ] **Gap #131: Emergency Change Authorization** (Week 7-8) — Fast-track procedures

### Phase 6: Optimization & Scaling (Weeks 9-10)

**Original Gaps:**
- [ ] Gap #33-40: Agentic RAG & context engineering
- [ ] Gap #41-48: Agent roles & orchestration patterns
- [ ] Gap #72-82: Hierarchical decomposition & storage

### Phase 7: Future/Regulated (As Needed)

**NEW from Claude:**
- [ ] **Gap #121: Shared Context Poisoning** — If/when multi-user implemented
- [ ] **Gap #124: Hardware-Backed Identity** — HSM/TPM (P0 for regulated industries)
- [ ] **Gap #125: Confidential Computing** — AMD SEV / Intel TDX (P0 for regulated industries)

---

## Files Requiring Updates

### Documentation (High Priority)
- [ ] `docs/OBSERVABILITY.md` — Add rogue agent drift detection ✅
- [ ] `docs/SECURITY.md` — Add NHI observability, OWASP Agent Top 10
- [ ] `docs/ARCHITECTURE.md` — Add verification architecture, Agent OS
- [ ] `docs/AGENTIC-CONSENT.md` — Add JIT prompting, dynamic governance
- [ ] `backend/AGENT.md` — Add NHI definition-of-done gate

### New Documentation Required
- [ ] `docs/MEMORY-ARCHITECTURE.md`
- [ ] `docs/IDENTITY-PROPAGATION.md`
- [ ] `docs/AGENT-OS.md`
- [ ] `docs/CONSENSUS-MODEL.md`
- [ ] `docs/NHI-OBSERVABILITY.md`

### Backend Implementation
- [ ] Create `backend/agents/verification/`
- [ ] Create `backend/agents/adversarial/`
- [ ] Create `backend/memory/` module
- [ ] Create `backend/security/vault.py`
- [ ] Update `backend/graph/builder.py` (consensus workflow)
- [ ] Update `backend/schemas/envelope.py` (add violation tracking)
- [ ] Create `backend/security/nhi_registry.py`

### Frontend
- [ ] Update `frontend/components/ConsentPromptModal.tsx` (OWASP Agent #9)
- [ ] Add `frontend/components/ReasoningTrace.tsx` (observability)

---

## Testing Requirements

### New Test Suites Required
- [ ] `backend/tests/architecture/test_consensus.py`
- [ ] `backend/tests/memory/test_episodic.py`
- [ ] `backend/tests/security/test_nhi.py`
- [ ] `backend/tests/security/test_vault.py`
- [ ] `backend/tests/security/test_owasp_agent_top10.py`
- [ ] `backend/tests/observability/test_drift_detection.py`

---

## Recommendations

### 📋 Epic Ticket Creation Workflow

**Each week of gap remediation requires structured planning:**

**Week 1 (Current):**
- ✅ Epic Ticket: `docs/jira-tickets-json/DB-E8-gap-remediation.json` (Created)
- ✅ Implementation Guide: `docs/gaps/WEEK1-IMPLEMENTATION-GUIDE.md`
- ✅ Kickoff Prompt: `docs/gaps/KICKOFF-PROMPT.md`

**Future Weeks (Create AFTER previous week completes):**
- [x] Week 2: `DB-E9-gap-remediation-week2.json` + guides
- [x] Week 3: `DB-E10-gap-remediation-week3.json` + guides
- [x] Week 4: `DB-E11-gap-remediation-week4.json` + guides
- [x] Week 5: `DB-E12-gap-remediation-week5.json` + guides (**DB-E2 `Description` format required**)
- [ ] Week 6-8: Continue pattern (DB-E13 through DB-E15)

**Ticket format (required for DB-E12 onward):** Use flat-array DB-E2 shape with rich `Description` per task — sections `IMPLEMENTATION DETAILS`, `EFFORT`, `PROJECT AREA`, `DEPENDENCIES`, `TESTING CRITERIA`, `EDGE CASES`. Canonical reference: `docs/jira-tickets-json/DB-E2-mvp2-agents.json`, `docs/jira-tickets-json/README.md`.

**See:** `docs/gaps/WEEK2-PLANNING.md` for guidance on creating subsequent week materials.

---

### Immediate Actions (This Week)
1. **Update OBSERVABILITY.md** with rogue agent drift detection (Gap #99) ✅
2. **Create NHI registry** and document pre-merge gate (Gap #93)
3. **Design verification agent** architecture (Gaps #1-2)
4. **Document credential vault** requirements (Gap #19)

### MVP Scope Adjustments
- **MVP 2**: Add Verification Agent before Calendar Agent
- **MVP 3**: Add NHI observability alongside OpenTelemetry
- **MVP 4**: Add full HITL layers, not just consent
- **MVP 5**: Expand to OWASP Agent Top 10, not just LLM Top 10

### Documentation Standards
- All new agents require `AGENT.md` with memory requirements
- All security controls require test coverage
- All MCP integrations require security assessment in `docs/adr/`

---

## Conclusion

The current proposal (v1.5.0) provides a solid foundation with strong OWASP GenAI Top 10 coverage and robust security controls. However, **121 total gaps** (99 from IBM analysis + 22 from Claude Zero-Trust) must be addressed before production deployment.

**Critical Findings (67 gaps not implemented):**

### From IBM Analysis
1. **Multi-agent verification architecture** (consensus model) — Gaps #1-7
2. **Last-mile identity & JIT credentials** (zero-trust completion) — Gaps #18-20
3. **Four-layer memory architecture** (CoALA compliance) — Gaps #8-13
4. **Rogue agent drift detection** (OWASP Agent #10) — Gap #99
5. **NHI observability** (non-human identity management) — Gaps #92-94

### NEW from Claude Zero-Trust Analysis
6. **Spotlighting for indirect injection** (calendar/email attacks) — Gap #114 ⚠️ P0
7. **Tool poisoning defense** (MCP validation) — Gap #117 ⚠️ P0
8. **Confused deputy prevention** (delegation framework) — Gap #118 ⚠️ P0
9. **Supply chain security** (AI-BOM, OpenSSF Scorecard) — Gaps #115-#116
10. **Constitutional classifiers** (95% jailbreak block) — Gap #126

**Priority Breakdown:**
- **P0 Critical:** 24 gaps (18 original + 6 Claude)
- **P1 High:** 52 gaps (39 original + 13 Claude)
- **P2 Medium:** 38 gaps (35 original + 3 Claude)
- **P3 Low:** 7 gaps

**Estimated Effort:** 9-10 weeks for full remediation across all 7 phases.

**For detailed Claude alignment analysis, see:** `docs/gaps/CLAUDE-ZERO-TRUST-ALIGNMENT.md`

---

*Gap Analysis Review — Created June 4, 2026 | Updated June 6, 2026 (Claude Zero-Trust alignment)*
