# Adversarial Agent Quality Checklist

**Version:** 1.0.0

---

Before returning output, verify:

- [ ] Valid JSON matching `output-schema.md`
- [ ] Each challenge has `target`, `concern`, `alternative`, `severity`
- [ ] `risk_level` aligns with challenge severities
- [ ] `recommended_action` consistent with severe count (2+ severe → `reject`)
- [ ] Challenges are specific, not generic ("plan might be wrong")
- [ ] No markdown outside JSON
- [ ] Alternatives are actionable interpretations, not vague warnings
