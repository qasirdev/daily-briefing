# Critic Agent Output Schema

**Version:** 2.0.0

---

```json
{
  "approved": true,
  "issues": ["string"]
}
```

## Field Rules

| Field | Type | Required | Notes |
|---|---|---|---|
| `approved` | boolean | Yes | `false` triggers revision when under cycle limit |
| `issues` | string[] | Yes | Empty when approved with no concerns |

## Examples

**Approved:**
```json
{"approved": true, "issues": []}
```

**Revision required:**
```json
{
  "approved": false,
  "issues": ["Focus plan missing summary", "No time blocks allocated for Q2 report"]
}
```

**Degraded approve (cycle 2 exhausted):**
```json
{
  "approved": true,
  "issues": ["Summary still vague after revision"]
}
```
