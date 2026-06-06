# ADR: Week 5 Supply Chain Security & JIT Credentials

**Status:** Accepted  
**Date:** 2026-06-06  
**Epic:** DB-E12

---

## Context

Gap remediation Phase 3 requires AI-BOM tracking, dependency auditing, tamper-evident audit logs, and JIT credential mediation for MCP integrations (Gaps #115, #116, #19, #123, #127).

---

## Decisions

### 1. AI-BOM format and location

- **Decision:** YAML manifest at `infrastructure/ai-bom.yaml` validated by `scripts/validate_ai_bom.py` in CI.
- **Rationale:** Human-readable, diff-friendly, aligns with proposal v2.0.0 project structure.
- **Alternatives considered:** CycloneDX JSON only — rejected for agent readability.

### 2. OpenSSF Scorecard in CI

- **Decision:** Document ≥7.0 threshold and manual weekly run; **pip-audit blocks CI** on critical/high CVEs.
- **Rationale:** Scorecard CLI requires GitHub API access and adds CI complexity; pip-audit gives immediate CVE signal.

### 3. Audit log storage

- **Decision:** Hash-chain logic in `backend/security/audit.py` with in-memory writer for runtime; Alembic `007_audit_log_sealed` for PostgreSQL persistence schema.
- **Rationale:** Separates security audit from `backend/memory/audit.py` (memory read trail).

### 4. Credential broker modes

- **Decision:** `VAULT_MODE=env` (default) mediates refresh token with consent + audit; `memory` mode exchanges OAuth access tokens with in-memory TTL cache.
- **Rationale:** Backward compatible with existing stdio Calendar MCP env vars during migration.

### 5. Calendar MCP integration

- **Decision:** `CalendarMCPStdioClient` rebuilds subprocess env from broker on each `call_tool` call.
- **Rationale:** Stdio spawns per call — enables JIT credential injection without long-lived token in client constructor.

---

## Consequences

- CI requires `pyyaml` and `pip-audit` (dev dependency).
- Operators must keep `infrastructure/ai-bom.yaml` updated when changing LLM or embedding models.
- Production should migrate `VAULT_MODE` to `memory` with Redis/Vault backend (future work).
