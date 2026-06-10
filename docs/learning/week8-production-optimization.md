# Week 8 Learnings — Production Optimization & Agentic RAG

**Date:** 2026-06-06  
**Epic:** DB-E15

---

## Key Implementations

### Agentic RAG

Static always-on retrieval replaced with `decide_retrieval()` — skips semantic for first-time users, full retrieval for rich MCP context, iterative query refinement when semantic hits are empty.

### Context Engineering

Four IBM pillars documented in `CONTEXT-ENGINEERING.md` and mapped to existing modules rather than new infrastructure.

### Reasoning Feedback

`POST /api/v1/feedback/reasoning` stores per-agent ratings into episodic memory with `feedback_type=reasoning_feedback`. Frontend `ReasoningFeedback` buttons on each trace step.

### T1087 Enumeration

`EnumerationDetector` tracks consent-list and credential-issue probes per user; threshold breach fires MITRE T1087 detection + security alert.

### Deployment Gates

`check_deployment_gates()` evaluates MITRE coverage, alert investigation rate, agentic RAG flag, and compression budget.

---

## Patterns to Reuse

- Decision engine before expensive vector search (cost + latency win)
- Compression as last mile before LLM injection
- Episodic memory as universal feedback sink (output edits + reasoning ratings)

---

*Week 8 Learning Doc — Created 2026-06-06*
