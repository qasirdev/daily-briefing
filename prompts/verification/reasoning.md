# Verification Agent Reasoning

**Version:** 1.0.0

---

## Decision Framework

```
FOR each claim in focus_output:
  IF no MCP field supports claim → flag critical
  ELIF MCP field contradicts claim → flag major or critical by impact
  ELIF claim is subjective summary → flag minor OR verify as stylistic
  ELSE → add to verified_claims
```

## Thinking Template

```
<thinking>
1. MCP tasks: [count, key deadlines]
2. MCP events: [count, time ranges]
3. Focus claims extracted: [list]
4. Mismatches: [claim → MCP truth]
5. Severity assignment: [rationale]
6. Confidence: [score]
</thinking>
```

## Independence Rule

Do not use Focus Agent reasoning or `<thinking>` blocks. Only compare final claims to MCP fields.
