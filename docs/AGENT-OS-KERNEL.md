# Agent OS Kernel

**Version:** 2.0.0 | **Last Updated:** June 2026

The Agent OS Kernel provides foundational services for all briefing agents. Implementation lives in `backend/kernel/`.

| Component | Module | Responsibility |
|---|---|---|
| Scheduler | `kernel/scheduler.py` | Canonical agent invocation order |
| Memory Manager | `kernel/memory_manager.py` | CoALA four-layer memory facade |
| Tool Manager | `kernel/tool_manager.py` | MCP allowlists, chaining limits, response validation |
| Identity Manager | `kernel/identity_manager.py` | Delegation tokens and JIT credentials |
| Security Monitor | `kernel/security_monitor.py` | Drift detection and dwell-time tracking |

MCP ingress validation and spotlighting are applied in `backend/mcp/ingress.py` and agent nodes before LLM processing.
