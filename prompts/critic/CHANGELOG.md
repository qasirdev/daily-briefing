# Critic Prompt Changelog

## [2.0.0] - 2026-06-06

### Added (DB-120)
- Full v2.0.0 11-file prompt structure aligned with Focus and Verification agents
- `context.md`, `instructions.md`, `examples.md`, `output-schema.md`, `reasoning.md`, `quality-checklist.md`
- Static prefix sized for OpenAI automatic prompt caching (≥1024 tokens)
- Explicit revision budget and consensus interaction guidance

### Changed
- `system.md` expanded with identity, responsibilities, and agent boundaries
- CONTRACT bumped to 2.0.0; node uses `resolve_prompt_version("critic")`

### Deprecated
- v1.5.0 single-file assembly path (retained files for reference; v2 activates via `instructions.md`)

## [1.5.0] - 2026-05-XX

- Initial critic prompt with guardrails and tools
