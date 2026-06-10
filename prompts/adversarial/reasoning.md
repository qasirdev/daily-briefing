# Adversarial Agent Reasoning

**Version:** 1.0.0

---

## Red Team Framework

```
ASSUME plan is flawed
FOR each time block, priority, and meeting reference:
  ASK "what would make this wrong?"
  ASK "what did the user not see?"
  ASK "what changes if data is stale?"
RECORD challenge with alternative
```

## Thinking Template

```
<thinking>
1. Strongest claims in focus plan: [...]
2. Verification gaps (passed but fragile): [...]
3. Edge cases from scenarios 1–5: [...]
4. Severe vs moderate classification: [...]
5. recommended_action rationale: [...]
</thinking>
```

## Scenario Triggers

- Priority inversion → challenge task ordering
- Overlap risk → challenge calendar gap assumptions
- Stale data → challenge completed-but-listed tasks
- Verification blind spot → challenge technically-correct but misleading claims
