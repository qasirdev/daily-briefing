# KICKOFF PROMPT — Week 1 Implementation: Multi-Agent Consensus Model

**Epic:** Week 1 Gap Remediation — Multi-Agent Verification Architecture  
**Integration Branch:** `epic/autonomus-implementation-gap`  
**Feature Branch:** `epic/week1-gap-remediation`  
**Duration:** 5 days (40 hours)  
**Implementation Agents:** Coding → Refactor → Testing → Documentation (see `.cursor/rules/`)

---

## 🎯 Mission

Implement the multi-agent consensus model (Generator → Verification → Adversarial → Consensus) to address critical gaps identified in the IBM recommendation review.

**Epic Ticket:** `docs/jira-tickets-json/DB-E8-gap-remediation.json`  
**Tasks:** DB-101 (Day 1) through DB-105 (Day 5)

**Primary Deliverables:**
1. Drift detection observability (Gaps #99) — DB-101
2. NHI registry for all agents (Gaps #92-93) — DB-102
3. Verification & Adversarial agent architecture (Gaps #1-2) — DB-103
4. Consensus workflow in LangGraph (Gaps #3-5) — DB-104
5. Integration tests & documentation — DB-105

**Note:** This is Week 1 of the gap remediation roadmap. See "Week 2 Planning" section at the end of this document for creating subsequent week tickets.

---

## 📖 Mandatory Reading (Execute BEFORE Implementation)

**Read in this exact order:**

1. ✅ `AGENT.md` — Root workflow rules (10 min)
2. ✅ `docs/EXECUTION-RULES.md` — Production-ready code requirements (15 min)
3. ✅ `docs/TOKEN-EFFICIENCY.md` — Context management (5 min)
4. ✅ `docs/tasks/lessons.md` — Avoid repeating past mistakes (5 min)
5. ✅ `backend/AGENT.md` — Backend agent rules (10 min)
6. ✅ `docs/ENGINEERING-STANDARDS.md` — Coding standards (20 min)
7. ✅ `docs/example-code/examples/s1-d1-python-for-fastapi-engineers-update1.md` — Reference implementations (30 min)
8. ✅ `docs/gaps/WEEK1-IMPLEMENTATION-GUIDE.md` — Complete implementation guide (45 min)
9. ✅ `docs/gaps/GAP-ANALYSIS-REVIEW.md` — Context for gaps being addressed (20 min)
10. ✅ `docs/guidence/2026-12-01-youtube-IBM.md` — IBM multi-agent recommendations (30 min)

**Total Reading Time:** ~3 hours (REQUIRED before writing any code)

---

## 🚨 Pre-Implementation Checklist

**Complete ALL items before starting Day 1:**

### Git & Environment Setup

```bash
# 1. Ensure on integration branch
git checkout epic/autonomus-implementation-gap
git pull origin epic/autonomus-implementation-gap

# 2. Create Week 1 epic branch
git checkout -b epic/week1-gap-remediation
git push -u origin epic/week1-gap-remediation

# 3. Verify Python version
python --version  # Must be 3.12+

# 4. Update dependencies
uv sync

# 5. Run baseline tests
uv run pytest -v

# 6. Create logs directory for test output capture
mkdir -p logs

# 7. Verify MCP connections
# Test PostgreSQL MCP
# Test Calendar MCP
```

### Task Planning (CRITICAL — Per EXECUTION-RULES.md §2.2)

**Create implementation plan in `docs/tasks/todo.md` BEFORE touching any code:**

```bash
# Open todo.md and add Week 1 plan
cat >> docs/tasks/todo.md << 'EOF'

# Week 1 Implementation — Multi-Agent Consensus Model

## Epic: Gap Remediation Week 1
Branch: epic/week1-gap-remediation
Status: in_progress
Started: [DATE]

### Day 1: Drift Detection & Observability (Gap #99)
- [ ] Update backend/schemas/envelope.py with GuardrailViolation
- [ ] Create backend/observability/metrics.py
- [ ] Write tests: backend/tests/observability/test_drift_detection.py
- [ ] Verify: All tests pass with ACTUAL metrics (not mocked)
- [ ] Update docs/tasks/todo.md — mark Day 1 complete
- [ ] Update docs/tasks/lessons.md with insights
- [ ] Commit: "Day 1: Drift detection implementation with tests"

### Day 2: NHI Registry Foundation (Gaps #92-93)
- [ ] Create docs/NHI-OBSERVABILITY.md
- [ ] Create backend/security/nhi_registry.py
- [ ] Write tests: backend/tests/security/test_nhi.py
- [ ] Verify: Registry JSON persists correctly
- [ ] Update docs/tasks/todo.md — mark Day 2 complete
- [ ] Update docs/tasks/lessons.md with insights
- [ ] Commit: "Day 2: NHI registry with 5 registered agents"

### Day 3: Verification Agent Design (Gaps #1-2)
- [ ] Read existing AGENT.md files (task, calendar, focus, critic, orchestrator)
- [ ] Create backend/agents/verification/AGENT.md (all required sections)
- [ ] Create backend/agents/adversarial/AGENT.md (all required sections)
- [ ] Verify: AGENT.md files complete and consistent
- [ ] Update docs/tasks/todo.md — mark Day 3 complete
- [ ] Update docs/tasks/lessons.md with design decisions
- [ ] Commit: "Day 3: Verification and Adversarial agent design specs"

### Day 4: Consensus Model Implementation (Gaps #3-5)
- [ ] Update backend/graph/builder.py with consensus workflow
- [ ] Create backend/agents/consensus/node.py
- [ ] Create backend/agents/verification/node.py (stub)
- [ ] Create backend/agents/adversarial/node.py (stub)
- [ ] Verify: Graph compiles without errors
- [ ] Update docs/tasks/todo.md — mark Day 4 complete
- [ ] Update docs/tasks/lessons.md with implementation insights
- [ ] Commit: "Day 4: Consensus model implementation in LangGraph"

### Day 5: Testing & Documentation
- [ ] Write integration tests: backend/tests/architecture/test_consensus.py
- [ ] Update docs/ARCHITECTURE.md with consensus workflow
- [ ] Create docs/learning/week1-consensus-pattern.md
- [ ] Capture proof package in proof/week1/
- [ ] Update docs/tasks/todo.md — mark Day 5 complete
- [ ] Update docs/tasks/lessons.md with all Week 1 learnings
- [ ] Commit: "Week 1 complete: Multi-agent consensus implementation"

## Verification Gates
- ✅ Each day's tests must pass before proceeding
- ✅ No pseudo-code — only production-ready implementations
- ✅ All metrics wired to actual telemetry (OpenTelemetry)
- ✅ Each agent returns AgentResultEnvelope
- ✅ Context checkpoint at ~75% usage

## Checkpoint Protocol
If context reaches 75%, write to docs/tasks/checkpoint.md and commit WIP

EOF
```

### Feature Flag Setup

```bash
# Add consensus feature flag to .env
echo "ENABLE_CONSENSUS_WORKFLOW=false" >> .env

# This allows testing without affecting production workflow
# Week 1: flag=false (testing), Week 2: flag=true (production)
```

---

## 🤖 Cursor Agent Workflow (4-Agent Sequential Pattern)

Per `AGENT.md` and `.cursor/rules/`, execute in this order:

### 1️⃣ Coding Agent (`.cursor/rules/coding.mdc`)

**Scope:** Implementation of core functionality

**Days 1-4 Responsibilities:**
- Update schemas with violation tracking
- Implement metrics and observability layer
- Create NHI registry with persistence
- Design AGENT.md specifications
- Implement consensus workflow in LangGraph
- Create consensus evaluator node

**Hand-off to Refactor Agent when:**
- All code is written and compiles
- Basic functionality works (manual verification)
- Ready for optimization and schema validation review

---

### 2️⃣ Refactor Agent (`.cursor/rules/refactor.mdc`)

**Scope:** Schema validation, optimization, sanitization

**Responsibilities:**
- Verify all Pydantic v2 schemas use `ConfigDict`
- Ensure `Field(..., description="...")` on all model fields
- Validate `frozen=True` on immutable models
- Check type hints are complete (`str | None`, not `Optional[str]`)
- Verify no hardcoded values or pseudo-code remains
- Optimize imports (stdlib → third-party → local)
- Run `mypy --strict` and fix all type errors
- Run `ruff check` and `ruff format`

**Hand-off to Testing Agent when:**
- Code passes `mypy --strict` with zero errors
- Code passes `ruff check` with zero warnings
- All schemas validated and optimized

---

### 3️⃣ Testing Agent (`.cursor/rules/testing.mdc`)

**Scope:** OWASP GenAI boundary tests, integration tests

**Days 1-2 Responsibilities:**
- Write `backend/tests/observability/test_drift_detection.py` (7 tests)
- Write `backend/tests/security/test_nhi.py` (7 tests)
- Ensure tests use actual metrics (not mocked)
- Verify test coverage ≥80%

**Day 5 Responsibilities:**
- Write `backend/tests/architecture/test_consensus.py` (3 integration tests)
- Test all consensus scenarios (agreement, disagreement, minor)
- Capture test output to `logs/` directory
- Create proof package

**Hand-off to Documentation Agent when:**
- All tests pass (`uv run pytest -v`)
- Test coverage meets minimum (80%)
- Test output captured in `logs/` directory

---

### 4️⃣ Documentation Agent (`.cursor/rules/docs.mdc`)

**Scope:** AGENT.md creation, architecture updates, knowledge capture

**Day 3 Responsibilities:**
- Create `backend/agents/verification/AGENT.md` (all required sections)
- Create `backend/agents/adversarial/AGENT.md` (all required sections)
- Review for consistency with existing agent AGENT.md files

**Day 5 Responsibilities:**
- Update `docs/ARCHITECTURE.md` with consensus workflow
- Create `docs/learning/week1-consensus-pattern.md`
- Update `docs/tasks/todo.md` — mark all tasks complete
- Update `docs/tasks/lessons.md` with all Week 1 learnings
- Create proof package in `proof/week1/`

**Final Deliverable:**
- All documentation complete and cross-referenced
- All learnings captured for future reference

---

## 📋 Daily Workflow Template

**Execute this pattern for EACH day:**

### Morning: Pre-Work Checklist

```bash
# 1. Read lessons learned
cat docs/tasks/lessons.md

# 2. Review current task in todo.md
cat docs/tasks/todo.md | grep -A 10 "Day N"

# 3. Check git status
git status
git log --oneline -5

# 4. Verify tests still pass
uv run pytest -v
```

### Implementation: Execute Day's Tasks

**Follow WEEK1-IMPLEMENTATION-GUIDE.md for specific code examples**

1. **Coding Agent** — Implement functionality
2. **Refactor Agent** — Optimize and validate schemas
3. **Testing Agent** — Write tests and verify
4. **Documentation Agent** — Update docs

### End of Day: Verification Gate

```bash
# 1. Run all tests
uv run pytest -v > logs/day-N-test-output.txt

# 2. Verify mypy passes
mypy --strict backend/

# 3. Verify ruff passes
ruff check backend/

# 4. Update todo.md
# Mark day's tasks complete

# 5. Update lessons.md
# Add any insights or corrections

# 6. Commit work
git add -A
git commit -m "Day N: [descriptive message]"
git push origin epic/week1-gap-remediation

# 7. Check context usage
# If approaching 75%, write checkpoint to docs/tasks/checkpoint.md
```

---

## 🎯 Success Criteria (Definition of Done)

### Code Quality
- ✅ All code passes `mypy --strict` (zero errors)
- ✅ All code passes `ruff check` (zero warnings)
- ✅ No pseudo-code or `// add logic here` comments
- ✅ All metrics wired to actual telemetry (not mocked)
- ✅ All schemas use Pydantic v2 patterns

### Testing
- ✅ Test coverage ≥80%
- ✅ All 17 tests pass (7 drift + 7 NHI + 3 consensus)
- ✅ Test output captured in `logs/` directory
- ✅ Integration tests use actual `AgentResultEnvelope` schemas

### Documentation
- ✅ 2 AGENT.md files created (verification, adversarial)
- ✅ `docs/ARCHITECTURE.md` updated with consensus workflow
- ✅ `docs/learning/week1-consensus-pattern.md` created
- ✅ `docs/tasks/todo.md` — all tasks marked complete
- ✅ `docs/tasks/lessons.md` — all learnings captured

### Git & Deliverables
- ✅ 5 commits (1 per day) with descriptive messages
- ✅ Branch `epic/week1-gap-remediation` pushed to remote
- ✅ Proof package created in `proof/week1/`
- ✅ Ready for PR to `epic/autonomus-implementation-gap`

---

## 🚧 Known Constraints & Guardrails

### Per EXECUTION-RULES.md

**MUST DO:**
- ✅ Write plan to `docs/tasks/todo.md` BEFORE coding
- ✅ Read `docs/tasks/lessons.md` at session start
- ✅ Update lessons.md after any correction
- ✅ Never mark done without proof (test logs, diffs)
- ✅ Check `docs/SECURITY.md` before modifying agent I/O
- ✅ All agents return `AgentResultEnvelope`
- ✅ Create AGENT.md for all new agents

**MUST NOT DO:**
- ❌ Implement before plan confirmed
- ❌ Mark done without evidence
- ❌ Apply hacky fixes
- ❌ Edit out-of-scope files
- ❌ Repeat documented mistakes
- ❌ Use pseudo-code in production
- ❌ Hardcode secrets or mock metrics

### Security First
- Check `docs/SECURITY.md` for OWASP GenAI protocols
- All external data is untrusted until validated
- No raw strings from sub-agents (only JSON via Pydantic)
- Orchestrator-as-Presenter pattern (only Orchestrator synthesizes markdown)

---

## 📦 End of Week 1: Merge Protocol

**After all 5 days complete:**

```bash
# 1. Create proof package
mkdir -p proof/week1
cp logs/day1-test-output.txt proof/week1/
cp logs/day2-test-output.txt proof/week1/
cp logs/day5-integration-tests.txt proof/week1/
cp backend/security/nhi_registry.json proof/week1/
git log --oneline --graph > proof/week1/git-history.txt

# 2. Final verification
uv run pytest -v  # All tests pass
mypy --strict backend/  # Zero errors
ruff check backend/  # Zero warnings

# 3. Push epic branch
git push origin epic/week1-gap-remediation

# 4. Create PR to epic/autonomus-implementation-gap
# PR Title: "Week 1: Multi-Agent Consensus & NHI Registry"
# PR Body: Link to proof package and completed deliverables checklist

# 5. After CI passes and PR approved, merge
git checkout epic/autonomus-implementation-gap
git merge --no-ff epic/week1-gap-remediation
git push origin epic/autonomus-implementation-gap

# 6. Delete local branch (keep remote per EXECUTION-RULES.md §9)
git branch -d epic/week1-gap-remediation
# DO NOT run: git push origin --delete epic/week1-gap-remediation
```

---

## 🔄 Context Management

### Checkpoint Protocol (Per EXECUTION-RULES.md §8)

**If context usage reaches ~75%:**

1. **Write checkpoint:**
```markdown
# Session Checkpoint — Week 1 Gap Remediation — [Timestamp]

## Current State
- **Epic:** Week 1 Gap Remediation
- **Branch:** epic/week1-gap-remediation
- **Current Day:** Day N
- **Task Status:** [in_progress|completed]

## Completed This Session
- [x] Day 1: Drift detection with tests
- [x] Day 2: NHI registry implementation

## In Progress
- [ ] Day N: [what was done, what remains]

## Files Modified
- backend/schemas/envelope.py — Added GuardrailViolation
- backend/observability/metrics.py — Created metrics
- [etc.]

## Decisions Made
- Decision 1: Used frozen=True for immutable envelopes
- Decision 2: [etc.]

## Next Steps
1. Complete Day N: [specific remaining work]
2. Start Day N+1: [etc.]

## Resume Command
\`\`\`
Continue Week 1 implementation from Day N.
Read docs/tasks/checkpoint.md for full context.
Branch: epic/week1-gap-remediation
\`\`\`
```

2. **Commit checkpoint:**
```bash
git add docs/tasks/checkpoint.md
git commit -m "WIP: checkpoint at Day N - context handoff"
git push origin epic/week1-gap-remediation
```

3. **New session reads:**
- `docs/tasks/checkpoint.md`
- `docs/tasks/lessons.md`
- Current `docs/tasks/todo.md`

---

## 🎬 Ready to Begin?

**Confirm checklist complete:**

- [ ] Read all 10 mandatory documents (3 hours)
- [ ] Created epic branch: `epic/week1-gap-remediation`
- [ ] Written plan to `docs/tasks/todo.md`
- [ ] Created `logs/` directory
- [ ] Verified Python 3.12+ and `uv sync` complete
- [ ] Baseline tests pass
- [ ] Feature flag added to `.env`

**When ready, execute:**

```bash
# Start Day 1 implementation
# Coding Agent → Refactor Agent → Testing Agent → Documentation Agent

# Follow docs/gaps/WEEK1-IMPLEMENTATION-GUIDE.md for detailed code examples
```

---

**Good luck! Remember: Plan → Implement → Refactor → Test → Document → Verify → Commit**

---

## 📅 Week 2+ Planning Guidance

### Creating Week 2 Epic Ticket

**After Week 1 completion, create:**
- `docs/jira-tickets-json/DB-E9-gap-remediation-week2.json`
- `docs/gaps/WEEK2-IMPLEMENTATION-GUIDE.md`
- `docs/gaps/WEEK2-KICKOFF-PROMPT.md`

**Week 2 Focus Areas (from GAP-ANALYSIS-REVIEW.md):**

**High Priority Gaps (Week 2):**
1. **Four-Layer Memory Architecture (Gaps #6-12)**
   - Working Memory (ephemeral state)
   - Semantic Memory (vector search)
   - Procedural Memory (learned patterns)
   - Episodic Memory (interaction history)

2. **Prompt Version Management (Gaps #13-18)**
   - Semantic versioning for prompts
   - Prompt registry with rollback
   - A/B testing framework
   - Automated prompt optimization

3. **Advanced AgentOps (Gaps #19-25)**
   - Evaluation metrics (accuracy, latency, cost)
   - Batch evaluation framework
   - Human feedback loops
   - Performance benchmarking

**Ticket Creation Template:**

```json
{
  "epic": {
    "id": "DB-E9",
    "key": "DB-E9",
    "summary": "Week 2: Four-Layer Memory Architecture",
    "description": "Implement CoALA framework memory layers...",
    "status": "To Do",
    "priority": "High",
    "epic_link": "epic/autonomus-implementation-gap",
    "reference_docs": [
      "docs/gaps/GAP-ANALYSIS-REVIEW.md",
      "docs/gaps/WEEK2-IMPLEMENTATION-GUIDE.md"
    ]
  },
  "tasks": [
    {
      "id": "DB-106",
      "summary": "Day 1: Working Memory Implementation",
      "description": "Implement ephemeral working memory for agent state..."
    }
  ]
}
```

**Week 3-8 Epic IDs:**
- DB-E10: Week 3 — Prompt Version Management
- DB-E11: Week 4 — Advanced AgentOps & Evaluation
- DB-E12: Week 5 — Dynamic Credential Management
- DB-E13: Week 6 — Multi-Region Deployment
- DB-E14: Week 7 — Advanced Security Hardening
- DB-E15: Week 8 — Production Optimization

**See `docs/gaps/GAP-ANALYSIS-REVIEW.md` Section 5 (Remediation Roadmap) for complete 8-week breakdown.**

---

*Week 1 Kickoff Prompt — Created June 4, 2026*
