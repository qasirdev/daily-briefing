# Week 2 Planning — Gap Remediation Roadmap

**Status:** 🟢 In Progress (Week 1 complete — Option A + pgvector selected)  
**Prerequisites:** Week 1 (DB-E8) must be complete and merged ✅  
**Epic Ticket:** `docs/jira-tickets-json/DB-E9-gap-remediation-week2.json` ✅  
**Scope Decision:** Option A — caching Days 1-2, Working + Semantic Days 3-4, validation Day 5  
**Vector Store:** pgvector on Supabase (free tier compatible, RLS-native, matches v2.0.0 Postgres + Redis stack)

---

## 📝 Planning Protocol

**⚠️ IMPORTANT:** Do NOT create Week 2 materials until Week 1 is fully complete.

**Why?**
1. Week 1 implementation will surface new insights and architectural decisions
2. The actual codebase state after Week 1 informs Week 2 priorities
3. Learnings from Week 1 may change the approach to subsequent gaps
4. Dependencies and integration points become clearer after real implementation

**When to Create Week 2 Materials:**
- ✅ Week 1 (DB-E8) merged to `epic/autonomus-implementation-gap`
- ✅ All Week 1 tests passing (17 new + 116 baseline)
- ✅ `docs/tasks/lessons.md` updated with Week 1 learnings
- ✅ `docs/learning/week1-consensus-pattern.md` captured
- ✅ Proof package complete in `proof/week1/`

---

## 🎯 Week 2 Focus Areas

Based on `docs/gaps/GAP-ANALYSIS-REVIEW.md` and v2.0.0 proposal, Week 2 will address:

### Critical Priority: Prompt Caching Implementation (v2.0.0)

**Why Week 2:** Week 1 established cache metrics infrastructure; Week 2 implements actual caching for immediate ROI.

- **Claude Prompt Caching** — Implement `cache_control` blocks
  - Add cache markers to verification and adversarial agent prompts
  - Structure all prompts with static content before dynamic
  - Implement cache warming on application startup
  - Expected savings: 50-90% token cost reduction

- **OpenAI Prompt Caching** — Structure for automatic caching (≥1024 tokens)
  - Ensure system prompts exceed 1024 token threshold
  - Place examples and instructions before user input
  - Monitor cache hit rates via Week 1 metrics

- **Prompt Finalization** — Complete 11-file structure for verification and adversarial agents
  - Implement all 11 prompt files per agent (system.md, context.md, instructions.md, examples.md, output-schema.md, tools.md, reasoning.md, guardrails.md, quality-checklist.md, CHANGELOG.md, CONTRACT.md)
  - Apply v2.0.0 unified principles (Claude + OpenAI guidance)
  - Add model-specific configurations (effort, thinking, reasoning_effort, phase)
  - Integrate advanced patterns (verification loops, research mode, subagent control)

**Estimated Story Points:** 16 (Days 1-2, 8 per day)

---

### High Priority Gaps (P1)

#### 1. Four-Layer Memory Architecture (Gaps #6-12)
**CoALA Framework Implementation**

- **Working Memory** (Gap #6) — Ephemeral state management
  - Current agent state in LangGraph
  - Token budget tracking
  - Temporary context windows
  
- **Semantic Memory** (Gap #7) — Vector search for knowledge retrieval
  - Implement vector store (Pinecone/Weaviate)
  - Embed historical briefings
  - Similarity search for context

- **Procedural Memory** (Gap #8) — Learned patterns and optimizations
  - Store successful agent workflows
  - Pattern recognition from past executions
  - Optimization rules based on outcomes

- **Episodic Memory** (Gap #9) — Interaction history and user context
  - User preference tracking
  - Historical conversation logs
  - Temporal context awareness

#### 2. Memory Integration (Gaps #10-12)
- Cross-layer memory queries
- Memory consolidation strategies
- Memory retrieval optimization

**Estimated Story Points:** 24 (Days 3-5, 8 per day)

---

## 📋 Epic Ticket Format (Updated — DB-E12 onward)

**New gap-remediation epics (Week 5+) MUST use the DB-E2 flat-array format** with a rich `Description` column per task. Canonical examples: `DB-E2-mvp2-agents.json`, `DB-E12-gap-remediation-week5.json`. Full spec: `docs/jira-tickets-json/README.md`.

Each task `Description` must include: `IMPLEMENTATION DETAILS`, `EFFORT`, `PROJECT AREA`, `DEPENDENCIES`, `TESTING CRITERIA`, `EDGE CASES`.

**Backend verification gate (every task, before marking done):**

```bash
uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest
```

Weeks DB-E8–DB-E11 use the legacy `{ "epic": {...}, "tasks": [...] }` shape — do not copy that for new weeks.

---

## 📋 Week 2 Epic Ticket Template (Legacy)

**Create this file AFTER Week 1 complete:**  
`docs/jira-tickets-json/DB-E9-gap-remediation-week2.json`

```json
{
  "epic": {
    "id": "DB-E9",
    "key": "DB-E9",
    "summary": "Week 2: Prompt Caching + Four-Layer Memory Architecture",
    "description": "Implement prompt caching (v2.0.0) for immediate token cost reduction (50-90% savings, $20K/month ROI), complete 11-file prompt structures for verification and adversarial agents, and begin CoALA framework with four memory layers: Working, Semantic, Procedural, and Episodic.",
    "status": "To Do",
    "priority": "Critical",
    "assignee": "Cursor Agents (Coding → Refactor → Testing → Documentation)",
    "epic_link": "epic/autonomus-implementation-gap",
    "reference_docs": [
      "docs/gaps/GAP-ANALYSIS-REVIEW.md",
      "docs/gaps/WEEK2-IMPLEMENTATION-GUIDE.md",
      "docs/gaps/WEEK2-KICKOFF-PROMPT.md",
      "docs/learning/week1-consensus-pattern.md",
      "007-01-ai-daily-briefing-assistant-v2.0.0.md"
    ],
    "dependencies": [
      "DB-E8 (Week 1) must be complete and merged",
      "Cache metrics from Week 1 must be operational"
    ]
  },
  "tasks": [
    {
      "id": "DB-106",
      "summary": "Day 1: Claude Prompt Caching Implementation",
      "description": "Implement cache_control blocks in all agent prompts, restructure for optimal caching, add cache warming...",
      "story_points": 8
    },
    {
      "id": "DB-107",
      "summary": "Day 2: Complete 11-File Prompt Structure + OpenAI Caching",
      "description": "Finalize all 11 prompt files for verification and adversarial agents, optimize for OpenAI auto-caching (≥1024 tokens), validate cache hit rates...",
      "story_points": 8
    },
    {
      "id": "DB-108",
      "summary": "Day 3: Working Memory + Semantic Memory Foundation",
      "description": "Implement ephemeral working memory in LangGraph state, integrate vector database for semantic search...",
      "story_points": 8
    },
    {
      "id": "DB-109",
      "summary": "Day 4: Procedural Memory + Episodic Memory",
      "description": "Store successful agent workflows, track user interactions and preferences over time...",
      "story_points": 8
    },
    {
      "id": "DB-110",
      "summary": "Day 5: Memory Integration, Cache Performance Validation & Testing",
      "description": "Cross-layer queries, memory consolidation, cache ROI measurement, comprehensive tests...",
      "story_points": 8
    }
  ]
}
```

---

## 📚 Week 2 Documentation Checklist

**Create these files AFTER Week 1 complete:**

### Implementation Guide
**File:** `docs/gaps/WEEK2-IMPLEMENTATION-GUIDE.md`

**Contents:**
- [ ] Day-by-day breakdown (Days 1-5)
- [ ] Day 1-2: Prompt caching implementation with code examples
  - [ ] Claude cache_control block placement
  - [ ] OpenAI prompt structure for auto-caching (≥1024 tokens)
  - [ ] Cache warming strategies
  - [ ] Cache hit rate monitoring
- [ ] Day 2: Complete 11-file prompt structure for verification and adversarial agents
  - [ ] All 11 files per agent following v2.0.0 standards
  - [ ] Model-specific configurations (effort, thinking, reasoning_effort, phase)
  - [ ] Advanced prompting patterns (verification loops, research mode, subagent control)
- [ ] Days 3-5: Memory architecture code examples
  - [ ] Schema definitions (WorkingMemory, SemanticMemory, ProceduralMemory, EpisodicMemory)
  - [ ] Vector store integration (Pinecone/Weaviate)
  - [ ] Memory consolidation logic
- [ ] Testing strategy (caching ROI, memory persistence, retrieval accuracy)
- [ ] Verification gates per day

**Template:** Use `docs/gaps/WEEK1-IMPLEMENTATION-GUIDE.md` as template

### Kickoff Prompt
**File:** `docs/gaps/WEEK2-KICKOFF-PROMPT.md`

**Contents:**
- [ ] Mission statement (emphasize prompt caching as critical priority)
- [ ] Mandatory reading order (updated with Week 1 learnings + v2.0.0 proposal)
- [ ] Pre-implementation checklist (include cache metrics verification from Week 1)
- [ ] 4-agent workflow (Coding → Refactor → Testing → Documentation)
- [ ] Daily workflow template
- [ ] Success criteria (cache hit rate targets, memory performance benchmarks)
- [ ] Week 3 planning guidance

**Template:** Use `docs/gaps/KICKOFF-PROMPT.md` as template

### Learning Documentation
**File:** `docs/learning/week2-caching-and-memory.md`

**Contents:**
- [ ] Prompt caching implementation patterns
- [ ] Cache ROI analysis (actual vs. projected savings)
- [ ] CoALA framework implementation patterns
- [ ] Vector store selection and configuration
- [ ] Memory consolidation strategies
- [ ] Lessons learned from Week 2

---

## 🔄 Week-by-Week Planning Sequence

### After Week 1 Complete

1. **Review Week 1 learnings** — Read `docs/tasks/lessons.md`
2. **Analyze architecture changes** — Check `backend/graph/builder.py`
3. **Create Week 2 ticket** — `DB-E9-gap-remediation-week2.json`
4. **Write implementation guide** — `WEEK2-IMPLEMENTATION-GUIDE.md`
5. **Create kickoff prompt** — `WEEK2-KICKOFF-PROMPT.md`
6. **Execute Week 2**

### After Week 2 Complete

1. **Review Week 2 learnings**
2. **Create Week 3 ticket** — `DB-E10-gap-remediation-week3.json`
3. **Focus:** Prompt Version Management (Gaps #13-18)
4. **Execute Week 3**

### Continue Through Week 8

**Epic Sequence (Updated for v2.0.0):**
- DB-E8: Week 1 — Multi-Agent Consensus + Cache Metrics ✅
- DB-E9: Week 2 — **Prompt Caching + Memory Architecture** (Days 1-2: Caching, Days 3-5: CoALA)
- DB-E10: Week 3 — Prompt Version Management (Gaps #13-18)
- DB-E11: Week 4 — AgentOps & Evaluation (Gaps #19-25)
- DB-E12: Week 5 — Supply Chain + JIT Credentials (Gaps #115-116, #19, #123, #127) ✅ ticket created
- DB-E13: Week 6 — Multi-Region & DR
- DB-E14: Week 7 — Security Hardening
- DB-E15: Week 8 — Production Optimization

**Note:** Week 2 prioritizes prompt caching (Days 1-2) for immediate ROI before memory architecture (Days 3-5), reflecting v2.0.0 cost optimization focus.

---

## 🎯 Alternative: Flexible Week 2 Scoping

**If memory architecture proves too complex after Week 1, prioritize:**

### Option A: Prompt Caching + Partial Memory (Recommended)
**Days 1-2:** Prompt caching implementation (critical for ROI)
**Days 3-4:** Working Memory + Semantic Memory only
**Day 5:** Testing and cache performance validation

**Rationale:** Delivers immediate cost savings (50-90% token reduction) while establishing memory foundation. Procedural and Episodic memory can move to Week 3.

### Option B: Full Memory Architecture (If Week 1 reveals high memory needs)
**Day 1:** Working + Semantic memory
**Day 2:** Procedural + Episodic memory  
**Day 3:** Memory integration + cross-layer queries
**Days 4-5:** Prompt caching implementation

**Rationale:** Prioritize memory if Week 1 consensus workflow creates significant context management challenges.

### Option C: Prompt Optimization Focus (If caching shows extraordinary impact)
**Days 1-2:** Prompt caching implementation
**Day 3:** Complete all 11-file prompt structures (verification, adversarial)
**Day 4:** Prompt version management foundation (Gaps #13-18)
**Day 5:** A/B testing framework for prompt optimization

**Rationale:** Double down on prompt engineering if early cache metrics show >80% hit rates and exceptional ROI.

**Decision Point:** After Week 1 retrospective, choose based on:
- Cache metrics from Week 1 (if hit rate potential is >80%, prioritize caching)
- Complexity of consensus implementation (if high coordination overhead, prioritize memory)
- Agent count and coordination needs (more agents = more memory requirements)
- Memory requirements discovered in Week 1 (if agents struggle with context, prioritize memory)

---

## 📊 Success Metrics (Week 2)

**Prompt Caching Performance (Days 1-2):**
- Cache hit rate: ≥70% for repeated prompts (target from v2.0.0: 80-90%)
- Token cost reduction: ≥50% compared to Week 1 baseline
- First-cache latency: <200ms for cache warming
- Cache size: Stable (no unbounded growth)
- Projected monthly savings: ≥$10,000 (v2.0.0 target: $20,250/month at scale)

**Prompt Quality (Day 2):**
- All 22 prompt files (11 per agent) created and validated
- Each prompt file follows v2.0.0 standards (unified principles, model configs)
- examples.md contains ≥3 complete input/output pairs with reasoning traces
- reasoning.md includes decision trees and <thinking> templates
- quality-checklist.md provides comprehensive self-verification criteria

**Memory Layer Tests (Days 3-5):**
- Working memory: <10ms access time
- Semantic memory: <100ms vector search
- Procedural memory: Pattern match accuracy >90%
- Episodic memory: Temporal queries <50ms

**Integration Tests:**
- Cross-layer queries execute successfully
- Memory consolidation runs nightly
- No memory leaks after 1000 requests
- Vector store maintains consistency
- Cache + memory integration: no performance degradation

**Coverage:**
- Unit tests: ≥80% for each memory layer
- Integration tests: 10+ scenarios
- Performance tests: Latency benchmarks
- Cache tests: Hit/miss scenarios, warming validation

---

## 🚨 Dependencies & Prerequisites

### Technical
- ✅ Week 1 consensus workflow operational
- ✅ NHI registry tracking all agents
- ✅ Drift detection metrics baseline
- ✅ Cache metrics instrumented (cache_hit_rate, cache_miss_total, cache_hit_total, cache_size_bytes)
- [ ] Baseline cache hit rate measured (Week 1 end)
- ✅ Vector store selected: **pgvector on Supabase**
- [ ] Memory schema design reviewed
- [ ] Verification and adversarial agent prompts ready for caching optimization

### Documentation
- ✅ `docs/learning/week1-consensus-pattern.md` complete
- ✅ Week 1 retrospective in `docs/tasks/lessons.md`
- ✅ Updated `docs/ARCHITECTURE.md` with consensus flow
- ✅ v2.0.0 proposal with caching strategies and ROI projections
- [ ] Memory architecture design doc
- [ ] Cache warming strategy documented
- [ ] 11-file prompt structure template validated (prompts/focus/ reference)

### Infrastructure
- [ ] Vector store provisioned (if cloud)
- [ ] Memory persistence layer (Redis/PostgreSQL)
- [ ] Monitoring for memory operations
- [ ] Grafana dashboard updated with cache performance panels (from Week 1)
- [ ] Prometheus scraping cache metrics successfully

---

## 📝 Notes for Week 2 Planning

**Capture these during Week 1:**

### Prompt Caching Insights
- [ ] What is the baseline cache hit rate with current prompts?
- [ ] Which agent prompts are >1024 tokens (OpenAI auto-cache eligible)?
- [ ] Are there opportunities to increase static content for better caching?
- [ ] What is the actual token cost before caching implementation?
- [ ] Which prompts have the highest reuse potential?

### Architectural Insights
- [ ] How does consensus workflow affect memory needs?
- [ ] Which agents need which memory layers?
- [ ] Memory consolidation frequency?
- [ ] User context retention policies?

### Performance Considerations
- [ ] Memory access latency impact on briefing time?
- [ ] Vector store query limits?
- [ ] Memory size constraints per user?
- [ ] Cleanup/archival strategy?
- [ ] Cache eviction policies needed?

### Integration Points
- [ ] How does verification agent use semantic memory?
- [ ] Do adversarial agents need procedural memory?
- [ ] Episodic memory for consensus disagreements?
- [ ] Cache warming on agent initialization?
- [ ] Cache invalidation on prompt version updates?

---

*Week 2 Planning Document — Created June 4, 2026*  
*Update this document after Week 1 completion with actual implementation details*
