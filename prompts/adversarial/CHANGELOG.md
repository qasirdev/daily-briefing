# Adversarial Agent Changelog

## [1.1.1] - 2026-06-10

### Added
- `input-security.md` — challenge assumptions without amplifying injection

## [1.1.0] - 2026-06-06

### Changed
- Wired LLM-backed adversarial review with cached prompt assembly
- Static prompt blocks optimized for OpenAI auto-cache (≥1024 tokens) and Claude `cache_control`
- Prompt version bumped to v1.1.0 for cache-enabled production rollout

## [1.0.0] - 2026-06-06

### Added
- Initial 11-file prompt structure (v2.0.0 standards)
- Red-team challenge framework with severity levels
- Five documented red-team scenarios
- Consensus trigger rules (2+ severe → human escalation)
- Integration contract for adversarial review pipeline
