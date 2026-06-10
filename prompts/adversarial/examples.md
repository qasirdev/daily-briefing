# Adversarial Agent Examples

**Version:** 1.0.0

---

## Example 1: Approve — No Significant Challenges

```json
{
  "challenges": [],
  "risk_level": "low",
  "recommended_action": "approve"
}
```

---

## Example 2: Moderate — Request Clarification

```json
{
  "challenges": [
    {
      "target": "Q2 report time block (10:00–13:00)",
      "concern": "3-hour estimate may be optimistic if report requires stakeholder input",
      "alternative": "Split into 2h draft + 1h review buffer; deprioritize if meeting overruns",
      "severity": "moderate"
    }
  ],
  "risk_level": "medium",
  "recommended_action": "request_clarification"
}
```

---

## Example 3: Severe — Reject and Escalate

```json
{
  "challenges": [
    {
      "target": "No overlap noted between 14:00 and 14:30 meetings",
      "concern": "MCP shows overlapping events; user may miss one commitment",
      "alternative": "Flag conflict explicitly and shorten focus block",
      "severity": "severe"
    },
    {
      "target": "Low-priority infra task deferred",
      "concern": "Task title references production blocker; may be mislabeled low",
      "alternative": "Treat as high priority until owner confirms",
      "severity": "severe"
    }
  ],
  "risk_level": "high",
  "recommended_action": "reject"
}
```
