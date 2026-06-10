# Verification Agent Quality Checklist

**Version:** 1.0.0

---

Before returning output, verify:

- [ ] Valid JSON matching `output-schema.md`
- [ ] Every flagged claim includes `source_truth` from MCP data
- [ ] Severity matches impact (invented data = critical)
- [ ] `confidence` is between 0.0 and 1.0
- [ ] No markdown or prose outside JSON
- [ ] `verified_claims` only contains MCP-supported statements
- [ ] Missing MCP data escalated via critical flags, not silently approved
