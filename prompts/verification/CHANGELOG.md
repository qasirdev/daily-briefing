# Verification Agent Changelog

## [1.1.1] - 2026-06-10

### Added
- `input-security.md` — MCP-grounded verification with spotlighting and bypass resistance

## [1.1.0] - 2026-06-06

### Changed
- Wired LLM-backed verification with cached prompt assembly (`build_llm_messages`)
- Static prompt blocks optimized for OpenAI auto-cache (≥1024 tokens) and Claude `cache_control`
- Prompt version bumped to v1.1.0 for cache-enabled production rollout

## [1.0.0] - 2026-06-06

### Added
- Initial 11-file prompt structure (v2.0.0 standards)
- Fact-checking workflow against raw MCP responses
- DiscrepancyClaim output schema with severity levels
- Independence protocol (no Focus reasoning traces)
- Integration contract for consensus pipeline

### Security
- Spotlighting for untrusted MCP fields
- Injection pattern rejection in source data
