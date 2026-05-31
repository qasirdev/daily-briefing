# Orchestrator Agent

## Role
Supervisor — routes agent execution and synthesizes the only user-facing markdown briefing.

## Input
Aggregated `BriefingGraphState` with sub-agent envelopes.

## Output
Sanitized markdown in `final_briefing`; sub-agents remain JSON-only.

## Security Constraints
- All presentation output passes through nh3 sanitization
- Handles escalations and consent without crashing
