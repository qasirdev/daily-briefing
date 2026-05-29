# Example Code Directory — AI Daily Briefing Assistant

This directory contains reference implementations and code patterns for the project.

---

## Purpose

Before writing new code, consult this directory for:
- Established patterns in this codebase
- Correct usage of project conventions
- Examples of well-structured components

---

## Directory Structure

```
docs/example-code/
├── README.md                    # This file
├── agent-node-pattern.py        # LangGraph agent node template
├── mcp-client-pattern.py        # MCP client implementation
├── pydantic-schema-pattern.py   # Pydantic v2 schema examples
├── api-endpoint-pattern.py      # FastAPI endpoint template
├── component-pattern.tsx        # React component template
└── test-pattern.py              # pytest test structure
```

---

## Patterns to Add

As the codebase develops, add examples for:

### Backend (Python)

- [ ] `agent-node-pattern.py` — LangGraph node with AgentResultEnvelope
- [ ] `mcp-client-pattern.py` — MCP client with error handling
- [ ] `pydantic-schema-pattern.py` — Strict Pydantic v2 models
- [ ] `api-endpoint-pattern.py` — Rate-limited FastAPI endpoint
- [ ] `telemetry-pattern.py` — OpenTelemetry instrumentation

### Frontend (TypeScript)

- [ ] `component-pattern.tsx` — Server/Client component with sanitization
- [ ] `hook-pattern.ts` — Data fetching hook with error handling
- [ ] `zod-schema-pattern.ts` — Zod validation for API responses

### Testing

- [ ] `unit-test-pattern.py` — pytest-asyncio test structure
- [ ] `security-test-pattern.py` — Adversarial test examples
- [ ] `component-test-pattern.tsx` — Vitest component test

---

## Usage

```python
# Before implementing a new agent node, check:
# docs/example-code/agent-node-pattern.py

# Ensure your implementation follows the established pattern
```

---

*Last Updated: May 2026*
