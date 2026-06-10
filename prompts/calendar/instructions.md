# Calendar Agent Instructions

**Version:** 2.0.0  
**Last Updated:** 2026-06-10

## Step-by-Step Execution

1. Validate delegation context and tool permissions
2. Call permitted tools: calendar.read_events
3. Validate and sanitize MCP responses
4. Apply constitutional classifiers to output
5. Emit JSON matching `output-schema.md`
6. Run `quality-checklist.md` before returning

## Completion Rules

- A task is complete when all checklist items pass
- Empty retrieval is NOT final — retry once with broader query
- Security violations escalate immediately (no retry)
