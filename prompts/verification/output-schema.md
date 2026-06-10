# Verification Agent Output Schema

**Version:** 1.0.0

---

```json
{
  "status": "verified | discrepancies_found",
  "verified_claims": ["string"],
  "flagged_claims": [
    {
      "claim": "string",
      "issue": "string",
      "source_truth": "string",
      "severity": "minor | major | critical"
    }
  ],
  "confidence": 0.0
}
```

## Field Rules

| Field | Required | Notes |
|---|---|---|
| `status` | Yes | `discrepancies_found` if any major/critical flags |
| `verified_claims` | Yes | Human-readable claim strings that matched MCP |
| `flagged_claims` | Yes | Empty array if none |
| `confidence` | Yes | Float 0.0–1.0 |

## Severity Guide

| Severity | Example |
|---|---|
| `minor` | Subjective phrasing ("busy day") not in MCP |
| `major` | Wrong priority label, off-by-hours time |
| `critical` | Invented meeting or non-existent task |
