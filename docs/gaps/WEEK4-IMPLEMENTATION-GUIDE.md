# Week 4 Implementation Guide — Memory Security, AgentOps & Live Embeddings

**Target:** Phase 2 gap remediation — harden memory, live embeddings, AgentOps  
**Duration:** 5 days (40 hours)  
**Epic Ticket:** `docs/jira-tickets-json/DB-E11-gap-remediation-week4.json`  
**Prerequisites:** Week 3 (DB-E10) merged — all four CoALA layers + prompt versioning operational

---

## Implementation Protocol

### Mandatory Reading Order

1. `AGENT.md` — Root workflow rules
2. `docs/EXECUTION-RULES.md`
3. `docs/tasks/lessons.md` — Week 1–3 learnings
4. `docs/learning/week3-memory-and-versioning.md`
5. `007-01-ai-daily-briefing-assistant-v2.0.0.md` — § RAG Poisoning, § Metrics Registry
6. `docs/gaps/WEEK4-KICKOFF-PROMPT.md`

### Git Branch Workflow

```bash
git checkout epic/autonomus-implementation-gap
git pull origin epic/autonomus-implementation-gap
git checkout -b epic/week4-gap-remediation
git push -u origin epic/week4-gap-remediation
```

### Backend Verification Gate

Before marking any day or task complete:

```bash
uv run ruff check backend && uv run ruff format backend && uv run mypy backend && uv run pytest
```

---

## Day 1: Live Embedding API (DB-116)

### Goals

- Replace deterministic-only vectors with OpenRouter embeddings in production
- Preserve deterministic mode for CI and offline development
- Async embedding for Focus agent and retrieval pipeline

### Settings

| Env Var | Default | Description |
|---|---|---|
| `EMBEDDING_PROVIDER` | `deterministic` | `deterministic` or `openrouter` |
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` | OpenRouter model id |
| `SEMANTIC_MEMORY_EMBEDDING_DIM` | `1536` | Must match model dimensions |

### Key Files

| File | Change |
|---|---|
| `backend/settings.py` | `embedding_provider`, `embedding_model` |
| `backend/memory/embeddings.py` | `embed_text_async()`, OpenRouter client |
| `backend/agents/focus/node.py` | Use `await embed_text_async()` |
| `backend/memory/retrieval.py` | Use `await embed_text_async()` |
| `backend/observability/metrics.py` | `embedding_requests_total`, `embedding_duration_ms` |

---

## Day 2: RAG Poisoning Defense (DB-117, Gap #120)

### Goals

- Scan semantic memory content before ingestion
- Track provenance and content hash
- Reject injection patterns at store time

### Injection Patterns (minimum)

- "ignore previous instructions"
- "system prompt:"
- Embedded credential patterns (API keys, tokens)
- HTML/script tags in plain text content

### Schema Extension (migration 005)

```sql
ALTER TABLE semantic_memory ADD COLUMN source_trust VARCHAR(16) NOT NULL DEFAULT 'internal';
ALTER TABLE semantic_memory ADD COLUMN content_hash VARCHAR(64) NOT NULL DEFAULT '';
ALTER TABLE semantic_memory ADD COLUMN quarantined BOOLEAN NOT NULL DEFAULT false;
```

### Key Files

| File | Change |
|---|---|
| `backend/memory/ingestion.py` | `validate_semantic_content()`, `compute_content_hash()` |
| `backend/memory/semantic.py` | Call validation before store; exclude quarantined rows |
| `backend/alembic/versions/005_semantic_provenance.py` | Provenance + quarantine columns |

---

## Day 3: Memory Quarantine (DB-118, Gap #132)

### Goals

- Freeze suspected poisoned memory (no retrieval)
- Review workflow: quarantine → inspect → restore or delete
- Alert via metrics and audit log

### Quarantine Triggers

- Ingestion validation failure (auto-quarantine option)
- Guardrail violation spike referencing memory content
- Manual admin quarantine via API

### Key Files

| File | Change |
|---|---|
| `backend/memory/quarantine.py` | `quarantine_memory()`, `restore_memory()`, `delete_memory()` |
| `backend/memory/semantic.py` | Filter `quarantined = false` in search |
| `backend/memory/episodic.py` | Quarantine support for episodic rows |
| `backend/tests/memory/test_quarantine.py` | Quarantine + retrieval exclusion tests |

---

## Day 4: Privilege Retention + AgentOps (DB-119)

### Goals

- Gap #119: Never store credentials or active privileges in memory
- Gap #58-61: Expand AgentOps metrics registry
- Post-session episodic distillation in orchestrator

### Privilege Rules

1. Redact `admin`, `credential`, `token`, `password` patterns from episodic summaries
2. Store privileges in past tense: "User granted calendar access for session X"
3. Session boundary clears working memory; episodic never implies current privilege

### New Metrics

| Metric | Type | Purpose |
|---|---|---|
| `consensus_disagreement_total` | Counter | Multi-agent disagreements |
| `memory_consolidation_duration_seconds` | Histogram | Consolidation job latency |
| `memory_quarantine_total` | Counter | Quarantine actions |
| `embedding_requests_total` | Counter | Embedding API usage |

### Key Files

| File | Change |
|---|---|
| `backend/memory/episodic.py` | `sanitize_lesson_content()` |
| `backend/agents/orchestrator/node.py` | Post-session `distill_working_to_episodic()` |
| `docs/MEMORY-ARCHITECTURE.md` | Privilege lifecycle + quarantine docs |

---

## Day 5: Critic v2.0.0 + Validation (DB-120)

### Goals

- Full 11-file prompt structure for Critic (reference: `prompts/focus/`)
- Static prefix ≥1024 tokens for OpenAI auto-cache
- Memory security integration tests + proof package

### Critic Prompt Files Required

```
prompts/critic/
├── system.md
├── context.md
├── instructions.md
├── examples.md
├── output-schema.md
├── tools.md
├── reasoning.md
├── guardrails.md
├── quality-checklist.md
├── CHANGELOG.md
└── CONTRACT.md  (bump to v2.0.0)
```

### Deliverables

- `proof/week4/` — test output, git history
- `docs/learning/week4-memory-security-and-agentops.md`
- Updated `docs/OBSERVABILITY.md` with new metrics

---

## Success Criteria

| Metric | Target |
|---|---|
| Embedding API | OpenRouter path tested with mock; deterministic in CI |
| Ingestion block rate | 100% on known injection test corpus |
| Quarantine exclusion | Quarantined rows never returned in search |
| Privilege redaction | Zero credential patterns in episodic store tests |
| Test count | 230+ passing (+13 from Week 3 baseline) |

---

*Week 4 Implementation Guide — Created 2026-06-06*
