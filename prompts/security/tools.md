# Security Tools

| Tool | Scope |
|---|---|
| PromptInjectionDetector | Scan untrusted text (regex + normalisation + fuzzy match) |
| PromptGuardService | LlamaFirewall PromptGuard 2 ML classifier (`InputSecurityScanner` layer 2) |
| sanitize_markdown | Strip unsafe HTML in orchestrator output |
| PIIDetector / mask_pii | Mask sensitive data in logs and LLM payloads |
| SSRFValidator | Validate calendar MCP outbound URLs |
