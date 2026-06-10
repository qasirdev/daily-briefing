# Task Agent Quality Checklist

**Version:** 2.0.0

Before returning output, verify:

- [ ] Schema compliance (all required fields present)
- [ ] No user-facing markdown in agent JSON
- [ ] External content was spotlighted
- [ ] Constitutional classifiers passed
- [ ] Token budget within limits
- [ ] Escalation payload present when status is `escalated`
