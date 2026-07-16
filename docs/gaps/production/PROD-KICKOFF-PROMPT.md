# PRODUCTION KICKOFF PROMPT — Week 1: Security Hot Path

**Epic:** PROD Week 1 — Security Hot Path (P0)  
**Integration Branch:** `epic/autonomus-implementation`  
**Feature Branch:** `epic/prod-week1-security-hotpath`  
**Duration:** 5 days (40 hours)  
**Implementation Workflow:** Single pass per day — implement, refactor, test, and document inline.

**Execution cadence:** Complete Day 1 → verify tests → Day 2 → … through Day 5. One commit per day; PR after Week 1.

---

## 🎯 Mission

Implement production-critical security controls and infrastructure foundations to enable safe production deployment.

**Epic Ticket:** `docs/jira-tickets-json/DB-E16-production-week1.json` (to be created)  
**Tasks:** PROD-101 (Day 1) through PROD-105 (Day 5)

**Primary Deliverables:**
1. Runtime spotlighting for indirect injection defense (PROD-002) — Day 1
2. MCP response validator with 3-layer defense (PROD-003) — Day 2
3. Consensus workflow production enablement (PROD-001, PROD-005) — Day 3
4. Deep health checks for all dependencies (PROD-032) — Day 4
5. Database migration strategy (zero-downtime) (PROD-034) — Day 5

**Context:** This is PROD Week 1 of 9 production weeks. Current state: 436 tests passing, gap remediation Weeks 1-8 complete, v2.0.0 security architecture exists but **disabled by default**. Mission: Activate and validate production security posture.

---

## 📖 Mandatory Reading (Execute BEFORE Implementation)

**Read in this exact order:**

1. ✅ `AGENT.md` — Root workflow rules (10 min)
2. ✅ `docs/EXECUTION-RULES.md` — Production-ready code requirements (15 min)
3. ✅ `docs/TOKEN-EFFICIENCY.md` — Context management (5 min)
4. ✅ `docs/tasks/lessons.md` — Avoid repeating past mistakes (5 min)
5. ✅ `backend/AGENT.md` — Backend agent rules (10 min)
6. ✅ `docs/ENGINEERING-STANDARDS.md` — Coding standards (20 min)
7. ✅ `docs/gaps/production/PROD-GAP-ANALYSIS-REVIEW.md` — All 53 production gaps (60 min)
8. ✅ `docs/gaps/production/PROD-PROPOSAL-REVIEW-SUMMARY.md` — Executive summary (20 min)
9. ✅ `docs/gaps/production/PROD-WEEK1-IMPLEMENTATION-GUIDE.md` — Complete guide (45 min — to be created)
10. ✅ `docs/SECURITY.md` — Security framework (30 min)
11. ✅ `docs/MCP.md` — MCP security requirements (20 min)
12. ✅ `prompts/focus/input-security.md` — Spotlighting reference implementation (15 min)

**Total Reading Time:** ~4 hours (REQUIRED before writing any code)

---

## 🚨 Pre-Implementation Checklist

**Complete ALL items before starting Day 1:**

### Git & Environment Setup

```bash
# 1. Ensure on integration branch
git checkout epic/autonomus-implementation
git pull origin epic/autonomus-implementation

# 2. Create PROD Week 1 epic branch
git checkout -b epic/prod-week1-security-hotpath
git push -u origin epic/prod-week1-security-hotpath

# 3. Verify Python and Node versions
nvm use 22              # Calendar MCP requires Node 22+
node --version          # Must be 22+
uv run python --version # Must be 3.12+

# 4. Update dependencies
uv sync

# 5. Run baseline tests (should be 436 passed, 3 skipped)
uv run pytest -v

# 6. Verify all gap remediation tests pass
uv run pytest backend/tests/architecture/test_consensus.py -v
uv run pytest backend/tests/security/test_nhi.py -v
uv run pytest backend/tests/security/test_ai_bom.py -v

# 7. Check current consensus workflow status
grep "ENABLE_CONSENSUS_WORKFLOW" .env
# Should be: ENABLE_CONSENSUS_WORKFLOW=false (will enable Day 3)

# 8. Verify observability stack is running
docker ps | grep prometheus
docker ps | grep grafana
# If not running: cd docs/guidence/observability && docker compose -f docker-compose.observability.yml up -d
```

### Production Environment Baseline

```bash
# 1. Copy production env template
cp .env.production.example .env.production

# 2. Document current production config status
echo "# PROD Week 1 Baseline - $(date)" > docs/gaps/production/prod-week1-baseline.md
echo "## Configuration Status" >> docs/gaps/production/prod-week1-baseline.md
echo "- ENABLE_CONSENSUS_WORKFLOW=false (will enable Day 3)" >> docs/gaps/production/prod-week1-baseline.md
echo "- Spotlighting: Not implemented" >> docs/gaps/production/prod-week1-baseline.md
echo "- MCP Validator: Not implemented" >> docs/gaps/production/prod-week1-baseline.md
echo "- Deep Health Checks: Not implemented" >> docs/gaps/production/prod-week1-baseline.md
echo "- DB Migration Strategy: Not documented" >> docs/gaps/production/prod-week1-baseline.md

# 3. Capture current test count
uv run pytest --co -q | wc -l > docs/gaps/production/prod-week1-test-count-baseline.txt
```

### Task Planning (CRITICAL — Per EXECUTION-RULES.md §2.2)

**Create implementation plan in `docs/tasks/todo.md` BEFORE touching any code:**

```bash
cat >> docs/tasks/todo.md << 'EOF'

# PROD Week 1 Implementation — Security Hot Path

## Epic: Production Week 1 — Security Hot Path
Branch: epic/prod-week1-security-hotpath
Status: in_progress
Started: [DATE]
Integration: epic/autonomus-implementation

### Day 1: Runtime Spotlighting (PROD-002) ⚠️ P0

**Objective:** Implement Microsoft spotlighting technique to defend against indirect injection attacks via calendar events, task titles, and MCP responses.

**Deliverables:**
- [ ] Create `backend/security/spotlighting.py` with `spotlight_external_content()` function
- [ ] Wire spotlighting into MCP client (`backend/mcp/client.py`)
- [ ] Apply spotlighting to calendar agent (`backend/agents/calendar/node.py`)
- [ ] Apply spotlighting to task agent (`backend/agents/task/node.py`)
- [ ] Apply spotlighting to focus agent (memory retrieval) (`backend/agents/focus/node.py`)
- [ ] Load `prompts/focus/input-security.md` rules into system prompts
- [ ] Create injection test corpus: `backend/tests/security/test_spotlighting.py`
- [ ] Test injection success rate: >50% → <2% (target)
- [ ] Update `docs/SECURITY.md` with spotlighting implementation details
- [ ] Verify: All tests pass, spotlighting active for all external data

**Success Criteria:**
- ✅ 20+ injection attempts blocked (test corpus)
- ✅ Spotlighting markers visible in LLM prompts (via debug logs)
- ✅ Zero regressions in existing tests (436 → 436+)

**Edge Cases to Test:**
- Calendar event titles with embedded instructions
- Task descriptions with prompt injection
- MCP responses with malicious content
- Empty/null content handling
- Unicode/special character handling

**Commit:** "Day 1: Runtime spotlighting implementation with injection tests"

---

### Day 2: MCP Response Validator (PROD-003) ⚠️ P0

**Objective:** Implement 3-layer validation for all MCP tool responses (schema, sanitization, anomaly detection) to defend against tool poisoning attacks.

**Deliverables:**
- [ ] Create `backend/mcp/validator.py` with `MCPResponseValidator` class
- [ ] Layer 1: Schema validation (Pydantic models for calendar events, tasks)
- [ ] Layer 2: Output sanitization (nh3 for HTML, URL allowlist)
- [ ] Layer 3: Anomaly detection (2σ deviation from baseline size/field count)
- [ ] Wire validator into MCP client (all `call_tool()` responses)
- [ ] Enforce tool allowlist: calendar.read_events, tasks.list, tasks.update
- [ ] Add tool-chaining counter (max 3 sequential calls per agent)
- [ ] Create `backend/tests/security/test_tool_poisoning.py`
- [ ] Test: Schema violations rejected, oversized responses quarantined
- [ ] Update `docs/MCP.md` with validation layer documentation

**Success Criteria:**
- ✅ 15+ validation test cases passing
- ✅ Schema violations raise `ValidationError`
- ✅ Oversized responses (>2σ) logged and quarantined
- ✅ Tool allowlist enforced (disallowed tools rejected)

**Edge Cases to Test:**
- Calendar events with malformed dates (end < start)
- Task titles exceeding max_length (200 chars)
- HTML/JavaScript in text fields (should be stripped)
- URLs outside allowlist (should be rejected)
- Responses 10x larger than baseline (anomaly)

**Commit:** "Day 2: MCP response validator with 3-layer defense"

---

### Day 3: Consensus Workflow Production Enablement (PROD-001, PROD-005) ⚠️ P0

**Objective:** Enable consensus workflow in production configuration and validate performance meets SLOs (P95 latency <10s).

**Deliverables:**
- [ ] Update `.env.production.example` → `ENABLE_CONSENSUS_WORKFLOW=true`
- [ ] Update `backend/settings.py` with production recommendations (document defaults)
- [ ] Update `docs/guidence/docker-setup.md` with consensus enablement instructions
- [ ] Update `docs/ARCHITECTURE.md` with production consensus workflow diagram
- [ ] Run staging soak test (1 hour, 100 requests, consensus enabled)
- [ ] Measure P95 latency: Target <10s, Max acceptable 12s
- [ ] Document rollback procedure: flip flag to `false`, restart supervisord
- [ ] Validate: Verification + Adversarial agents active in trace
- [ ] Create performance proof package: `proof/prod-week1/consensus-latency.md`

**Success Criteria:**
- ✅ P95 latency <10s under load (100 requests)
- ✅ Verification agent invoked on 100% of requests
- ✅ Adversarial agent invoked on 100% of requests
- ✅ Consensus evaluation visible in orchestrator output
- ✅ Rollback procedure tested (off → on → off → on)

**Load Test Script:**
```python
# tests/load/test_consensus_performance.py
import asyncio
import time
from backend.graph.builder import build_briefing_graph

async def load_test_consensus():
    graph = build_briefing_graph()
    latencies = []
    
    for i in range(100):
        start = time.time()
        result = await graph.ainvoke({"user_id": f"test_{i}"})
        latency = time.time() - start
        latencies.append(latency)
        if i % 10 == 0:
            print(f"Request {i}: {latency:.2f}s")
    
    p95 = sorted(latencies)[95]
    assert p95 < 10.0, f"P95 latency {p95:.2f}s exceeds 10s SLO"
```

**Commit:** "Day 3: Consensus workflow production enablement with latency validation"

---

### Day 4: Deep Health Checks (PROD-032) ⚠️ P0

**Objective:** Implement deep health checks for all production dependencies (DB, Redis, MCP, LLM) to enable load balancer health monitoring.

**Deliverables:**
- [ ] Create `backend/api/v1/health.py` with `/health` (shallow) and `/health/deep` (deep)
- [ ] Shallow check: HTTP 200 if process alive
- [ ] Deep check: Test DB connection (`SELECT 1`), Redis (`PING`), MCP (stub call), LLM (test request)
- [ ] Return HTTP 503 if any dependency unhealthy
- [ ] Add health check tests: `backend/tests/api/test_health.py`
- [ ] Update `docker-compose.yml` with health check configuration
- [ ] Document health check endpoints: `docs/operations/HEALTH-CHECKS.md`
- [ ] Verify: Deep health fails when DB down, Redis down, LLM API key invalid

**Success Criteria:**
- ✅ `/health` returns 200 in <50ms
- ✅ `/health/deep` returns 200 when all dependencies healthy
- ✅ `/health/deep` returns 503 when any dependency unhealthy
- ✅ Health check results visible in JSON response

**Health Check Response Format:**
```json
{
  "status": "healthy",  // or "degraded"
  "checks": {
    "database": {"status": "healthy", "latency_ms": 5},
    "redis": {"status": "healthy", "latency_ms": 2},
    "mcp_postgres": {"status": "healthy", "latency_ms": 150},
    "mcp_calendar": {"status": "healthy", "latency_ms": 200},
    "llm_primary": {"status": "healthy", "model": "gpt-4o-mini"},
    "llm_fallback": {"status": "healthy", "model": "llama3.1-70b"}
  }
}
```

**Commit:** "Day 4: Deep health checks for all production dependencies"

---

### Day 5: Database Migration Strategy (PROD-034) ⚠️ P0

**Objective:** Document and test zero-downtime database migration strategy for production deployments.

**Deliverables:**
- [ ] Document migration safety rules: `docs/operations/DATABASE-MIGRATIONS.md`
  - Additive-only schema changes (add columns, tables)
  - No data migrations in schema DDL
  - Multi-phase migrations for breaking changes
- [ ] Create migration rollback procedure (downgrade script + data reconciliation)
- [ ] Create pre-deploy migration check script: `backend/scripts/pre_deploy_migration_check.py`
- [ ] Test migration on staging with production data volume (anonymized)
- [ ] Add migration health check: Compare schema version in DB vs code
- [ ] Document supervisord startup integration (alembic upgrade head)
- [ ] Test rollback: Upgrade → downgrade → upgrade (verify data integrity)

**Success Criteria:**
- ✅ Migration safety rules documented (additive-only, no data DDL)
- ✅ Pre-deploy check script prevents unsafe migrations
- ✅ Rollback procedure tested successfully
- ✅ Migration runs automatically on deploy (supervisord integration)

**Migration Safety Rules:**
```markdown
1. **Additive Only:** Only add columns, tables, indexes (never drop)
2. **No Data DDL:** Data migrations run separately after schema
3. **Multi-Phase Breaking Changes:**
   - Phase 1: Add new column (nullable)
   - Phase 2: Backfill data
   - Phase 3: Make column non-nullable
   - Phase 4: Drop old column (after 1 week)
4. **Rollback Ready:** Every migration has tested downgrade
5. **Schema Version Check:** Fail deploy if DB schema < code schema
```

**Commit:** "Day 5: Database migration strategy with zero-downtime procedures"

---

## Verification Gates

**After each day:**
- ✅ All tests pass (`uv run pytest -v`)
- ✅ Linting passes (`uv run ruff check backend && uv run mypy backend`)
- ✅ No pseudo-code — only production-ready implementations
- ✅ Documentation updated (`docs/SECURITY.md`, `docs/MCP.md`, etc.)
- ✅ Proof artifacts captured in `proof/prod-week1/`
- ✅ `docs/tasks/todo.md` updated (mark day complete)
- ✅ `docs/tasks/lessons.md` updated with insights

**Before PR (end of Week 1):**
- ✅ All PROD Week 1 deliverables complete
- ✅ Security hot path active (spotlighting, validation, consensus)
- ✅ Health checks operational
- ✅ Migration strategy documented and tested
- ✅ Test count increased: 436 → 470+ (estimated +34 tests)
- ✅ No regressions in existing tests
- ✅ `proof/prod-week1/` contains:
  - Injection test results (>95% blocked)
  - Consensus latency proof (P95 <10s)
  - Health check validation
  - Migration rollback proof

## Checkpoint Protocol

If context reaches 75%, write to `docs/tasks/checkpoint.md` and commit WIP.

EOF
```

---

## 🤖 Cursor Agent Workflow

**PROD Week 1 uses a single-pass workflow:** implement, refactor (`mypy`/`ruff`), test, and document in one session per day.

Per `AGENT.md` and `.cursor/rules/`, each day covers:

### 1️⃣ Coding Agent (`.cursor/rules/coding.mdc`)

**Scope:** Implementation of core functionality

**Days 1-5 Responsibilities:**
- Implement spotlighting module with marker injection
- Wire spotlighting into MCP client and agents
- Implement MCP response validator (3 layers)
- Enable consensus workflow in production config
- Implement deep health checks for all dependencies
- Document database migration strategy

**Hand-off to Refactor Agent when:**
- All code is written and compiles
- Basic functionality works (manual verification)
- Ready for linting and type checking

### 2️⃣ Refactor Agent (`.cursor/rules/refactor.mdc`)

**Scope:** Code quality, linting, type checking

**Responsibilities:**
- Run `uv run ruff check backend`
- Run `uv run mypy backend`
- Fix all linting errors
- Add missing type hints
- Simplify complex functions
- Remove dead code

**Hand-off to Testing Agent when:**
- All linting passes
- All type checks pass
- Code is production-ready

### 3️⃣ Testing Agent (`.cursor/rules/testing.mdc`)

**Scope:** Comprehensive test coverage

**Responsibilities:**
- Write security tests (spotlighting injection corpus)
- Write validation tests (MCP tool poisoning)
- Write integration tests (consensus latency)
- Write health check tests
- Write migration tests
- Verify >80% coverage for new code

**Hand-off to Documentation Agent when:**
- All tests pass
- Coverage targets met
- Edge cases tested

### 4️⃣ Documentation Agent (`.cursor/rules/docs.mdc`)

**Scope:** Documentation, proof artifacts, learning capture

**Responsibilities:**
- Update `docs/SECURITY.md` (spotlighting section)
- Update `docs/MCP.md` (validation layer)
- Create `docs/operations/HEALTH-CHECKS.md`
- Create `docs/operations/DATABASE-MIGRATIONS.md`
- Create proof package: `proof/prod-week1/`
- Update `docs/tasks/lessons.md` with insights

---

## 🎯 Success Criteria (Week 1)

**After PROD Week 1 completion:**

✅ **Security Hot Path Active:**
- Runtime spotlighting operational (>95% injection blocking)
- MCP response validator operational (3-layer defense)
- Consensus workflow enabled in production config
- P95 latency <10s validated under load

✅ **Infrastructure Foundations:**
- Deep health checks operational
- Database migration strategy documented and tested
- Zero-downtime migration procedures validated

✅ **Testing & Validation:**
- 34+ new tests added (spotlighting, validation, health, migration)
- All existing tests still passing (436 → 470+)
- Security test corpus: 20+ injection attempts blocked
- Performance validated: 100 requests, P95 <10s

✅ **Documentation:**
- `docs/SECURITY.md` updated (spotlighting)
- `docs/MCP.md` updated (validator)
- `docs/operations/HEALTH-CHECKS.md` created
- `docs/operations/DATABASE-MIGRATIONS.md` created
- `proof/prod-week1/` package complete

---

## 📝 Daily Commit Messages

**Day 1:**
```
Day 1: Runtime spotlighting implementation with injection tests

- Created backend/security/spotlighting.py with spotlight_external_content()
- Wired spotlighting into MCP client and all agents
- Added injection test corpus (20+ attack vectors)
- Validated >95% blocking rate
- Updated docs/SECURITY.md

PROD-002 (Spotlighting): 🔴 → ✅
Tests: 436 → 448 (+12)
```

**Day 2:**
```
Day 2: MCP response validator with 3-layer defense

- Created backend/mcp/validator.py with MCPResponseValidator
- Implemented schema validation, output sanitization, anomaly detection
- Added tool allowlist enforcement and chaining counter
- Created tool poisoning test suite (15+ test cases)
- Updated docs/MCP.md

PROD-003 (MCP Validator): 🔴 → ✅
Tests: 448 → 463 (+15)
```

**Day 3:**
```
Day 3: Consensus workflow production enablement with latency validation

- Enabled ENABLE_CONSENSUS_WORKFLOW=true in production config
- Validated P95 latency <10s under load (100 requests)
- Documented rollback procedure
- Updated docs/ARCHITECTURE.md and docs/guidence/docker-setup.md
- Created proof/prod-week1/consensus-latency.md

PROD-001 (Consensus): 🟡 → ✅
PROD-005 (Prod Config): 🟡 → ✅
Tests: 463 → 465 (+2 load tests)
```

**Day 4:**
```
Day 4: Deep health checks for all production dependencies

- Created backend/api/v1/health.py with /health and /health/deep endpoints
- Implemented dependency checks (DB, Redis, MCP, LLM)
- Added health check tests with failure scenarios
- Updated docker-compose.yml with healthcheck configuration
- Created docs/operations/HEALTH-CHECKS.md

PROD-032 (Health Checks): 🔴 → ✅
Tests: 465 → 470 (+5)
```

**Day 5:**
```
Day 5: Database migration strategy with zero-downtime procedures

- Created docs/operations/DATABASE-MIGRATIONS.md (safety rules)
- Created backend/scripts/pre_deploy_migration_check.py
- Tested migration rollback (upgrade → downgrade → upgrade)
- Documented supervisord integration (alembic upgrade head)
- Validated migration health check

PROD-034 (DB Migrations): 🔴 → ✅
Tests: 470 → 472 (+2 migration tests)
```

---

## 🚀 Week 2 Planning

**At the end of PROD Week 1:**

1. **Create PROD Week 2 epic ticket:**
   ```bash
   cp docs/jira-tickets-json/DB-E16-production-week1.json \
      docs/jira-tickets-json/DB-E17-production-week2.json
   # Update epic ID, tasks, and dates
   ```

2. **Create PROD Week 2 implementation guide:**
   ```bash
   cp docs/gaps/production/PROD-WEEK1-IMPLEMENTATION-GUIDE.md \
      docs/gaps/production/PROD-WEEK2-IMPLEMENTATION-GUIDE.md
   # Update for Week 2 focus: Infrastructure Foundations
   ```

3. **Create PROD Week 2 kickoff prompt:**
   ```bash
   cp docs/gaps/production/PROD-KICKOFF-PROMPT.md \
      docs/gaps/production/PROD-WEEK2-KICKOFF-PROMPT.md
   # Update for Week 2 tasks
   ```

4. **Update `docs/PLAN.md`:**
   - Mark PROD Week 1 ✅
   - Mark PROD Week 2 🔄

---

## 🔍 Troubleshooting

### Common Issues

**Issue: Tests failing after spotlighting**
- **Solution:** Check that `<<<EXTERNAL_CONTENT>>>` markers are present in prompts
- **Debug:** Add `print(prompt)` before LLM call to verify markers

**Issue: MCP validator rejecting valid responses**
- **Solution:** Check Pydantic schema matches actual MCP response format
- **Debug:** Log rejected responses, adjust schema

**Issue: Consensus latency exceeds 10s**
- **Solution:** Check if LLM API is slow (measure per-agent latency)
- **Debug:** Add timing spans in LangGraph nodes

**Issue: Health check failing intermittently**
- **Solution:** Increase connection timeouts for MCP/LLM checks
- **Debug:** Test each dependency check independently

---

*PROD Week 1 Kickoff — Created June 8, 2026*
