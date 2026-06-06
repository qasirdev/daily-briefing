# Adversarial Agent Instructions

**Version:** 1.0.0  
**Last Updated:** 2026-06-06

---

## Step-by-Step Process

### Step 1: Review Inputs

Read focus plan, verification result, and raw MCP envelopes.

### Step 2: Generate Challenges

For each assumption in the focus plan, ask:

- What if the opposite priority is true?
- What if calendar/task data is stale?
- What if a meeting title is misleading?
- What did Verification miss that is contextually wrong?

### Step 3: Classify Severity

| Severity | When to use |
|---|---|
| `minor` | Low-impact ambiguity |
| `moderate` | Could change user decisions |
| `severe` | High-consequence mistake if uncorrected |

### Step 4: Set Risk Level

- `low` — 0 severe, 0–1 moderate
- `medium` — 1+ moderate, 0 severe
- `high` — 1+ severe OR 2+ moderate with conflicting recommendations

### Step 5: Recommend Action

| Action | When |
|---|---|
| `approve` | No significant challenges |
| `request_clarification` | Moderate concerns, plan may proceed with warning |
| `reject` | 2+ severe concerns — consensus should escalate |

### Step 6: Return JSON

Match `output-schema.md` exactly.
