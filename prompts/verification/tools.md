# Verification Agent Tools

**Version:** 1.0.0

---

## Available Tools

The Verification Agent does **not** call MCP tools directly. It receives pre-fetched envelopes from graph state.

| Data Source | Provided By | Usage |
|---|---|---|
| Task MCP response | Task Agent node | Ground truth for tasks |
| Calendar MCP response | Calendar Agent node | Ground truth for events |
| Focus plan | Focus Agent node | Claims to verify |

## Rules

- Do NOT request new MCP calls during verification
- Do NOT mutate source data
- If MCP envelope is `failure` or empty, set `status="discrepancies_found"` with severity `critical` and note missing source
