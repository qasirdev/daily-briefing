# Security Agent Output Schema

**Version:** 2.0.0

---

## JSON Schema

```json
{
  "type": "object",
  "required": ["severity", "category", "retry_allowed"],
  "properties": {
    "severity": {
      "type": "string",
      "enum": ["low", "medium", "high", "critical"]
    },
    "category": {
      "type": "string",
      "enum": [
        "none",
        "injection_override",
        "jailbreak_roleplay",
        "embedded_system_directive",
        "exfiltration",
        "pii_leak",
        "policy_violation"
      ]
    },
    "escalation": {
      "type": ["string", "null"],
      "enum": ["security_violation_detected", null]
    },
    "retry_allowed": {
      "type": "boolean"
    },
    "matched_patterns": {
      "type": "array",
      "items": { "type": "string" }
    },
    "context": {
      "type": "string",
      "maxLength": 500
    }
  },
  "additionalProperties": false
}
```

## Validation Rules

- `severity` critical or high with injection → `escalation` must be `security_violation_detected`
- `retry_allowed` must be `false` when escalation is set
- Output must be pure JSON — no markdown fences
