# Adversarial Agent Output Schema

**Version:** 1.0.0

---

```json
{
  "challenges": [
    {
      "target": "string",
      "concern": "string",
      "alternative": "string",
      "severity": "minor | moderate | severe"
    }
  ],
  "risk_level": "low | medium | high",
  "recommended_action": "approve | request_clarification | reject"
}
```

## Field Rules

| Field | Required | Notes |
|---|---|---|
| `challenges` | Yes | Empty array if none |
| `target` | Per challenge | Specific plan element challenged |
| `concern` | Per challenge | Why it might fail |
| `alternative` | Per challenge | Alternative reading or action |
| `severity` | Per challenge | Drives consensus routing |
| `risk_level` | Yes | Aggregate assessment |
| `recommended_action` | Yes | Consensus input |

## Consensus Mapping

- 2+ `severe` → expect `reject` and human escalation path
- 1+ `moderate`, 0 severe → `request_clarification`, minor disagreement path
- 0 moderate, 0 severe → `approve`
