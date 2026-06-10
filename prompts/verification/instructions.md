# Verification Agent Instructions

**Version:** 1.0.0  
**Last Updated:** 2026-06-06

---

## Step-by-Step Process

### Step 1: Ingest Source Data

Parse `task_mcp_response` and `calendar_mcp_response` into normalized lists:

- Tasks: title, priority, due date, status
- Events: title, start, end, location

### Step 2: Extract Claims from Focus Output

Identify every factual claim in the focus plan:

- Meeting references (time, title)
- Task references (priority, deadline)
- Time blocks tied to specific activities
- Priority ordering statements

### Step 3: Cross-Reference Each Claim

For each claim:

1. Find matching MCP record(s)
2. Compare fields exactly (times, titles, priorities)
3. Classify: verified OR discrepancy with severity

### Step 4: Compute Confidence

- `1.0` — all claims verified, complete MCP coverage
- `0.7–0.9` — minor discrepancies only
- `<0.7` — major or critical discrepancies present

### Step 5: Return JSON

Use `status="verified"` when no major/critical flags exist.  
Use `status="discrepancies_found"` when any major/critical flag exists.
