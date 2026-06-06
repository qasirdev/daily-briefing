# Verification Agent Examples

**Version:** 1.0.0

---

## Example 1: All Claims Verified

**MCP Calendar:** Meeting "Sprint Review" at 14:00  
**Focus Claim:** "Sprint Review at 2pm"  
**Output:**

```json
{
  "status": "verified",
  "verified_claims": ["Sprint Review scheduled at 14:00"],
  "flagged_claims": [],
  "confidence": 1.0
}
```

---

## Example 2: Critical Time Mismatch

**MCP Calendar:** Meeting at 14:00  
**Focus Claim:** "Client call at 3pm"  
**Output:**

```json
{
  "status": "discrepancies_found",
  "verified_claims": [],
  "flagged_claims": [
    {
      "claim": "Client call at 3pm",
      "issue": "No 15:00 event in calendar; MCP shows 14:00 Sprint Review",
      "source_truth": "Sprint Review start: 14:00",
      "severity": "critical"
    }
  ],
  "confidence": 0.4
}
```

---

## Example 3: Minor Subjective Wording

**MCP:** 3 meetings scheduled  
**Focus:** "Busy day ahead"  
**Output:**

```json
{
  "status": "verified",
  "verified_claims": ["Three calendar events present"],
  "flagged_claims": [
    {
      "claim": "Busy day ahead",
      "issue": "Subjective assessment not explicitly in MCP fields",
      "source_truth": "3 calendar events",
      "severity": "minor"
    }
  ],
  "confidence": 0.85
}
```
