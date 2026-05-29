# AI Daily Briefing Assistant — Project Specification

**Version:** 1.5.0 (Revision 7)  
**Date:** May 2026  
**Status:** Specification Complete — Ready for Implementation  
**Architecture:** Multi-Agent Orchestration | MCP Servers | Cursor Development Agents  
**Deployment:** Single Docker Container with Advanced Security Posture

This represents the enterprise-hardened specification for the AI Daily Briefing Assistant. It integrates strict **OWASP GenAI Security** protocols, **Prompt Injection Defense**, and formalizes the **Orchestrator-as-Presenter** pattern for safe multi-agent response synthesis.

---

## MVP DELIVERY OVERVIEW

| Milestone | Scope Summary | Status |
|---|---|---|
| **MVP 1** | Next.js UI scaffold, FastAPI backend, LangGraph orchestration, basic MCP integration | Planned |
| **MVP 2** | PostgreSQL MCP, Task Agent, Calendar Agent, Focus Agent implementation | Planned |
| **MVP 3** | Critic Agent, DLQ routing, observability baseline, OpenTelemetry integration | Planned |
| **MVP 4** | Agentic Consent modal, Local LLM fallback, learner feedback loops | Planned |
| **MVP 5** | Comprehensive OWASP GenAI Security Hardening, Prompt Injection Defense | Planned |
| **MVP 6** | Orchestrator-as-Presenter finalization, production deployment, Docker signing | Planned |

---

## DESIGN PRINCIPLES & SECURITY

- **Zero-Trust Input (OWASP Top 10):** Calendar events and tasks are treated as untrusted inputs. They are sanitized for markdown/HTML execution and scanned for Prompt Injection attempts before being passed to LLMs.
- **Cryptographic Integrity:** Docker images are signed in CI. All MCP communications occur over local TCP or TLS. JWTs (`pyjwt[crypto]`) are enforced if externalized.
- **Orchestrator-as-Presenter:** The Orchestrator completely synthesizes multi-agent outputs. Individual agents (Doers/Planners) return raw Pydantic JSON; only the Orchestrator maps this into the user-facing format to ensure consistent tone and safety.
- **Circuit Breakers:** Exceeding 2x token budgets immediately circuit-breaks the agent, dropping the request to the DLQ to prevent denial-of-wallet attacks.
- **Agentic Consent:** Time-bounded, transaction-aware authorization for external services with JIT (Just-In-Time) re-authorization flows.

---

## TECHNOLOGY STACK

| Layer | Technology | Version |
|---|---|---|
| **Frontend** | Next.js (App Router) | 16.x |
| **React** | React with Server Components | 19.x |
| **Backend** | FastAPI | 0.115+ |
| **Python** | Python (managed by uv) | 3.12+ |
| **Validation** | Pydantic | 2.8+ |
| **Orchestration** | LangGraph | 0.4+ |
| **Observability** | OpenTelemetry | 1.28+ |
| **Process Manager** | Supervisord | 4.2.x |
| **Reverse Proxy** | Nginx | 1.27.x |

---

## AGENT ROLE FRAMEWORK

| Agent | Canonical Role | Responsibility | Tools / MCP | Security Posture |
|---|---|---|---|---|
| **Task Agent** | Doer | Reads/prioritizes tasks | PostgreSQL MCP | Read-only scope, RLS enforced |
| **Calendar Agent** | Tool Operator | Fetches today's events | Google Calendar MCP | Strict Allowlist, SSRF defense |
| **Focus Agent** | Planner | Generates work plan | LLM only | Instruction Hierarchy Enforced |
| **Critic Agent** | Critic (Safety+Quality) | Reviews for coherence and safety violations | LLM only | Final Output Gatekeeper |
| **Orchestrator** | Supervisor + Presenter | Assembles and sanitizes final UI output | — | Composes `AgentResultEnvelope` |

### Prompt Injection Defense Protocol

Calendar events created by third parties (e.g., meeting invites) are prime vectors for Indirect Prompt Injection.

1. Calendar MCP fetches raw event descriptions
2. The Critic Agent evaluates text using a lightweight classifier for injection signatures
3. If flagged, the payload is scrubbed or dropped before reaching the Focus Agent
4. The `AgentResultEnvelope` escalation reason is marked as `security_violation_detected` and is never retried

### Agent Communication Protocol

```json
{
  "agent_id": "calendar",
  "canonical_role": "tool_operator",
  "status": "success|failure|escalated",
  "result": { /* agent-specific payload */ },
  "metadata": {
    "execution_ms": 110,
    "tokens_used": 50,
    "model_used": "openai/gpt-4o-mini",
    "prompt_version": "v1.5.0",
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "data_classification": "confidential_pii"
  },
  "escalation": {
    "reason": "security_violation_detected|max_retries_exceeded|mcp_timeout|consent_required",
    "target_agent": "orchestrator",
    "context": "Additional debugging context"
  }
}
```

---

## MCP INTEGRATIONS

| MCP Server | Implementation Details | Security |
|---|---|---|
| **PostgreSQL MCP** | Tools: `list_tables`, `query`, `insert`. Manages tasks, preferences, DLQ | RLS enforced, read-only for agents |
| **Google Calendar MCP** | Tools: `list_calendars`, `get_events`. Time-bounded consent | SSRF defense, `*.googleapis.com` allowlist |

---

## CURSOR DEVELOPMENT AGENTS

| Cursor Agent | Scope | Rules File |
|---|---|---|
| **Coding Agent** | Implements endpoints, LangGraph, prompt injection defense | `.cursor/rules/coding.mdc` |
| **Testing Agent** | OWASP GenAI boundary tests, adversarial testing | `.cursor/rules/testing.mdc` |
| **Refactor Agent** | Schema validation, output sanitization, deduplication | `.cursor/rules/refactor.mdc` |
| **Documentation Agent** | AGENT.md files, security checklists, ADRs | `.cursor/rules/docs.mdc` |

---

## FULL PROJECT TREE

```text
daily-briefing/
├── AGENT.md                               # Root index with workflow rules
├── pyproject.toml                         # 'uv' managed dependencies
├── .env.example                           # Environment variable template
│
├── .cursor/
│   └── rules/
│       ├── coding.mdc                     # Python/TypeScript standards
│       ├── testing.mdc                    # Test coverage requirements
│       ├── refactor.mdc                   # Schema & sanitization rules
│       └── docs.mdc                       # Documentation standards
│
├── docs/
│   ├── tasks/
│   │   ├── todo.md                        # Active task tracking
│   │   └── lessons.md                     # Self-improvement log
│   ├── learning/                          # Knowledge capture
│   ├── adr/                               # Architectural Decision Records
│   ├── jira-tickets-json/                 # Epic/story/task definitions
│   │   └── README.md                      # JSON schema documentation
│   ├── ARCHITECTURE.md                    # System architecture & diagrams
│   ├── MCP.md                             # MCP tool schemas & security
│   ├── ENGINEERING-STANDARDS.md           # Twelve-Factor, dependencies
│   ├── OBSERVABILITY.md                   # Metrics, tracing, SLOs
│   ├── DATA-OWNERSHIP.md                  # GDPR, retention, portability
│   ├── AGENTIC-CONSENT.md                 # Consent flows, token lifecycle
│   ├── LOCAL-LLM.md                       # Fallback models, benchmarks
│   └── SECURITY.md                        # OWASP GenAI, injection defense
│
├── frontend/
│   ├── AGENT.md                           # Frontend development rules
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── api/auth/callback/google/
│   ├── components/
│   │   ├── BriefingDashboard.tsx
│   │   ├── ObservabilityBadge.tsx
│   │   └── ConsentPromptModal.tsx
│   ├── hooks/
│   ├── lib/
│   └── __tests__/
│
├── backend/
│   ├── AGENT.md                           # Backend development rules
│   ├── main.py
│   ├── settings.py
│   ├── api/v1/
│   ├── agents/
│   │   ├── AGENT.md                       # Multi-agent rules
│   │   ├── orchestrator/
│   │   │   └── AGENT.md
│   │   ├── task/
│   │   │   └── AGENT.md
│   │   ├── calendar/
│   │   │   └── AGENT.md
│   │   ├── focus/
│   │   │   └── AGENT.md
│   │   └── critic/
│   │       └── AGENT.md
│   ├── graph/
│   ├── mcp/
│   ├── llm/
│   ├── schemas/
│   ├── security/
│   └── tests/
│
├── prompts/
│   ├── AGENT.md                           # Prompt engineering standards
│   ├── orchestrator/
│   │   ├── CONTRACT.md
│   │   ├── CHANGELOG.md
│   │   ├── system.md
│   │   ├── skills.md
│   │   ├── tools.md
│   │   └── guardrails.md
│   ├── task/
│   ├── calendar/
│   ├── focus/
│   ├── critic/
│   └── security/
│       ├── CONTRACT.md
│       ├── system.md
│       └── guardrails.md
│
└── infrastructure/
    ├── AGENT.md                           # CI/CD rules
    ├── docker-compose.yml
    ├── Dockerfile
    ├── nginx.conf
    └── supervisord.conf
```

---

## DOCUMENTATION REFERENCE

| Document | Purpose | Lines |
|---|---|---|
| `AGENT.md` (root) | Workflow rules, MVP tracking, agent framework | ~150 |
| `docs/ARCHITECTURE.md` | Deployment topology, data flows, state schema | ~300 |
| `docs/SECURITY.md` | OWASP Top 10 compliance, injection defense | ~340 |
| `docs/ENGINEERING-STANDARDS.md` | Twelve-Factor, dependencies, Docker build | ~280 |
| `docs/MCP.md` | Tool schemas, security constraints, error handling | ~535 |
| `docs/OBSERVABILITY.md` | Metrics registry, SLOs, alert rules | ~410 |
| `docs/DATA-OWNERSHIP.md` | GDPR compliance, retention, PII handling | ~300 |
| `docs/AGENTIC-CONSENT.md` | Consent flows, token lifecycle, revocation | ~350 |
| `docs/LOCAL-LLM.md` | Model benchmarks, hardware requirements | ~450 |
| `frontend/AGENT.md` | Component specs, sanitization, accessibility | ~407 |
| `backend/AGENT.md` | Envelope schema, node patterns, error handling | ~512 |
| `prompts/AGENT.md` | Prompt versioning, instruction hierarchy | ~462 |

---

## OWASP GenAI TOP 10 COVERAGE

| ID | Vulnerability | Mitigation | Status |
|---|---|---|---|
| LLM01 | Prompt Injection | Critic Agent scanning, input sanitization | Specified |
| LLM02 | Insecure Output | DOMPurify (FE), nh3 (BE), Orchestrator-as-Presenter | Specified |
| LLM03 | Training Data Poisoning | N/A (no custom training) | N/A |
| LLM04 | Model DoS | Token budgets, circuit breakers, rate limiting | Specified |
| LLM05 | Supply Chain | Dependency scanning, lockfile pinning | Specified |
| LLM06 | Sensitive Info Disclosure | PII masking, data classification | Specified |
| LLM07 | Insecure Plugin Design | MCP allowlists, SSRF defense | Specified |
| LLM08 | Excessive Agency | Read-only scopes, explicit tool boundaries | Specified |
| LLM09 | Overreliance | N/A (UX concern) | N/A |
| LLM10 | Model Theft | N/A (no proprietary models) | N/A |

---

## IMPLEMENTATION ARTIFACTS

| Artifact | Purpose | Location |
|---|---|---|
| Epic JSON Files | 52 tasks across 6 MVPs | `docs/jira-tickets-json/DB-E*.json` |
| Kick-off Prompt | Ready-to-use autonomous start | `docs/KICKOFF-PROMPT.md` |
| Checkpoint File | Context handoff between sessions | `docs/tasks/checkpoint.md` |
| Progress Tracker | Implementation status | `docs/PLAN.md` |
| Execution Rules | Workflow discipline | `docs/EXECUTION-RULES.md` |

---

## AUTONOMOUS WORKFLOW

### Agent Execution Order (Per Epic)
```
1. Coding Agent    → Implement all tasks
2. Refactor Agent  → Code quality review
3. Testing Agent   → Add tests, verify coverage
4. Docs Agent      → Update documentation
5. Merge to main   → After all checks pass
```

### Context Management
- At 75% context usage: write checkpoint, spawn continuation
- Checkpoint file: `docs/tasks/checkpoint.md`
- Resume with compacted context from checkpoint

### Branch Strategy
```bash
git checkout -b epic/E1-project-scaffold  # MVP 1
git checkout -b epic/E2-core-agents       # MVP 2
git checkout -b epic/E3-observability     # MVP 3
git checkout -b epic/E4-agentic-consent   # MVP 4
git checkout -b epic/E5-security-hardening # MVP 5
git checkout -b epic/E6-production        # MVP 6
```

---

## KICK-OFF

To start autonomous implementation:

1. Copy contents of `docs/KICKOFF-PROMPT.md` into a new chat
2. Agent will read AGENT.md and begin with Epic DB-E1
3. Monitor progress via `docs/PLAN.md` and `docs/tasks/todo.md`
4. On checkpoint: start new session with continuation prompt

---

*Project Specification — Version 1.5.0 (Revision 7) — May 2026*
