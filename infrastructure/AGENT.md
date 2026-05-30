# Infrastructure Agent

**Version:** 1.6.0 | **Last Updated:** May 2026

## Scope

CI/CD, GitHub branch policy, and deployment rules for the AI Daily Briefing Assistant.

---

## GitHub Branch Policy

| Branch | Purpose |
|---|---|
| `epic/autonomus-implementation` | Long-lived integration branch — all epics merge here |
| `epic/E{n}-{short-description}` | Short-lived per-epic work branch |
| `main` | Not used for epic merges during autonomous implementation |

### Epic-to-Epic Flow

1. Branch from latest `epic/autonomus-implementation`
2. Push `epic/E{n}-...`; implement → refactor → test → docs
3. Open PR with base `epic/autonomus-implementation`
4. Merge with a **merge commit** after CI passes (not squash or rebase)
5. Pull integration branch; delete **local** epic branch
6. **Do not** delete the remote epic branch on GitHub
7. Start next epic from updated `epic/autonomus-implementation`

### Post-Merge Commands

```bash
git checkout epic/autonomus-implementation
git pull origin epic/autonomus-implementation
git branch -d epic/E{n}-{short-description}
```

Canonical reference: `docs/EXECUTION-RULES.md` Section 9.

---

## CI Triggers

- Push to `epic/autonomus-implementation`
- Pull requests targeting `epic/autonomus-implementation`

See `.github/workflows/ci.yml` (created in Epic DB-E1).

---

*Infrastructure Agent — Version 1.6.0 — May 2026*
