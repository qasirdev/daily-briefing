# Adversarial Agent Tools

**Version:** 1.0.0

---

## Available Tools

The Adversarial Agent performs **read-only analysis** on graph state. No MCP or LLM tool calls.

| Input | Source | Purpose |
|---|---|---|
| Task MCP envelope | Graph state | Alternative priority interpretations |
| Calendar MCP envelope | Graph state | Conflict and overlap analysis |
| Focus plan | Graph state | Assumption targets |
| Verification result | Graph state | Blind-spot detection |

## Rules

- Do NOT invoke MCP servers
- Do NOT modify graph state
- Do NOT re-run Verification — build on its output
