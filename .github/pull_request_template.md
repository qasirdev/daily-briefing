## Summary

<!-- What changed and why -->

## Security checklist

- [ ] OWASP GenAI controls reviewed (`docs/SECURITY.md`)
- [ ] No secrets or PII in logs, tests, or fixtures
- [ ] Output sanitization applied for user-facing content
- [ ] Rate limits and token budgets unchanged or intentionally updated
- [ ] Security tests under `backend/tests/security/` pass

## Test plan

- [ ] `uv run ruff check backend`
- [ ] `uv run mypy backend`
- [ ] `uv run pytest`
