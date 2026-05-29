# Architectural Decision Records (ADR) — AI Daily Briefing Assistant

This directory contains Architectural Decision Records documenting significant technical decisions.

---

## Purpose

Create an ADR when:
- Choosing between competing technologies
- Making irreversible architectural decisions
- Establishing patterns that affect multiple components
- Changing existing architectural decisions

---

## File Naming Convention

```
ADR-NNN-short-description.md
```

Examples:
- `ADR-001-langgraph-for-orchestration.md`
- `ADR-002-orchestrator-as-presenter.md`
- `ADR-003-local-llm-fallback-strategy.md`

---

## Template

```markdown
# ADR-NNN: [Decision Title]

**Status:** [Proposed | Accepted | Deprecated | Superseded by ADR-XXX]
**Date:** YYYY-MM-DD
**Authors:** [Names or 'Cursor Agent']

## Context

What is the issue that we're seeing that motivates this decision?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

### Positive
- What becomes easier

### Negative
- What becomes more difficult

### Neutral
- Other impacts

## Alternatives Considered

### Alternative 1: [Name]
- Description
- Why rejected

### Alternative 2: [Name]
- Description
- Why rejected

## References

- Links to relevant documentation
- Related ADRs
```

---

## Index

| ADR | Title | Status | Date |
|---|---|---|---|
| — | No ADRs created yet | — | — |

---

## Pending Decisions

Decisions that may need ADRs during implementation:

1. **Database choice** — PostgreSQL vs SQLite for single-user MVP
2. **MCP server implementation** — Existing MCP servers vs custom
3. **Authentication** — JWT vs session-based for consent tokens
4. **Deployment target** — Container Apps vs ECS vs bare Docker

---

*Last Updated: May 2026*
