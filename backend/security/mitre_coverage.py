"""MITRE ATT&CK detection coverage registry (Gap #129)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

CoverageStatus = Literal["detected", "partial", "not_applicable", "blind_spot"]


@dataclass(frozen=True, slots=True)
class TechniqueMapping:
    """Maps a MITRE ATT&CK technique to a detection control."""

    technique_id: str
    name: str
    tactic: str
    status: CoverageStatus
    detection_control: str
    metric_or_audit: str
    notes: str = ""


TECHNIQUE_REGISTRY: tuple[TechniqueMapping, ...] = (
    TechniqueMapping(
        "T1566.001",
        "Spearphishing Attachment",
        "Initial Access",
        "detected",
        "InputSecurityScanner on calendar/email-derived text",
        "security_violations_total",
    ),
    TechniqueMapping(
        "T1566.002",
        "Spearphishing Link",
        "Initial Access",
        "partial",
        "SSRFValidator on MCP URLs",
        "security_violations_total",
        notes="Link content in events scanned at ingestion",
    ),
    TechniqueMapping(
        "T1190",
        "Exploit Public-Facing Application",
        "Initial Access",
        "detected",
        "SlowAPI rate limits + circuit breakers",
        "rate_limit_exceeded audit",
    ),
    TechniqueMapping(
        "T1078",
        "Valid Accounts",
        "Credential Access",
        "detected",
        "JIT CredentialBroker + consent validation",
        "credential_issuance_total",
    ),
    TechniqueMapping(
        "T1550.001",
        "Application Access Token",
        "Defense Evasion",
        "detected",
        "Short-lived credentials (TTL ≤900s)",
        "audit_log credential_issued",
    ),
    TechniqueMapping(
        "T1550.004",
        "Web Session Cookie",
        "Defense Evasion",
        "partial",
        "Session timeout targets in SECURITY.md",
        "consent_expired audit",
    ),
    TechniqueMapping(
        "T1071",
        "Application Layer Protocol",
        "Command and Control",
        "detected",
        "MCP domain allowlists",
        "ssrf_blocked security log",
    ),
    TechniqueMapping(
        "T1048",
        "Exfiltration Over Alternative Protocol",
        "Exfiltration",
        "detected",
        "PIIDetector + local LLM routing",
        "pii_detected_and_masked log",
    ),
    TechniqueMapping(
        "T1498",
        "Network Denial of Service",
        "Impact",
        "detected",
        "Token budgets + rate limits",
        "token_budget_exceeded",
    ),
    TechniqueMapping(
        "T1499",
        "Endpoint Denial of Service",
        "Impact",
        "detected",
        "Graph circuit breaker",
        "dlq_events_total",
    ),
    TechniqueMapping(
        "T1565",
        "Data Manipulation",
        "Impact",
        "detected",
        "Read-only SQL + MCP write scope denial",
        "test_mcp_security.py",
    ),
    TechniqueMapping(
        "T1565.001",
        "Stored Data Manipulation",
        "Impact",
        "detected",
        "Memory quarantine on poisoned entries",
        "memory_quarantine_total",
    ),
    TechniqueMapping(
        "T1213",
        "Data from Information Repositories",
        "Collection",
        "detected",
        "ABAC consent + scoped MCP access",
        "consent_granted audit",
    ),
    TechniqueMapping(
        "T1087",
        "Account Discovery",
        "Discovery",
        "detected",
        "EnumerationDetector on consent/credential probes",
        "security_enumeration_attempts_total",
    ),
    TechniqueMapping(
        "T1059",
        "Command and Scripting Interpreter",
        "Execution",
        "not_applicable",
        "No arbitrary code execution by agents",
        "N/A",
    ),
    TechniqueMapping(
        "T1027",
        "Obfuscated Files or Information",
        "Defense Evasion",
        "detected",
        "Unicode NFKC normalization before scan",
        "constitutional_violations_total",
    ),
    TechniqueMapping(
        "T1036",
        "Masquerading",
        "Defense Evasion",
        "detected",
        "Constitutional impersonation rules",
        "constitutional_violations_total",
    ),
    TechniqueMapping(
        "T1485",
        "Data Destruction",
        "Impact",
        "detected",
        "Agents prohibited from delete operations",
        "test_agent_scope.py",
    ),
    TechniqueMapping(
        "T1530",
        "Data from Cloud Storage",
        "Collection",
        "detected",
        "Consent-gated calendar MCP reads",
        "credential_issuance_total",
    ),
    TechniqueMapping(
        "T1212",
        "Exploitation for Credential Access",
        "Credential Access",
        "detected",
        "Sealed audit log + vault broker",
        "audit_log_entries_total",
    ),
    TechniqueMapping(
        "T1195",
        "Supply Chain Compromise",
        "Initial Access",
        "detected",
        "AI-BOM + pip-audit CI gates",
        "validate_ai_bom.py",
    ),
    TechniqueMapping(
        "T1598",
        "Phishing for Information",
        "Reconnaissance",
        "detected",
        "Spotlighting + constitutional classifiers",
        "security_violations_total",
    ),
)


def get_technique(technique_id: str) -> TechniqueMapping | None:
    """Return mapping for a MITRE technique ID."""
    normalized = technique_id.upper()
    for mapping in TECHNIQUE_REGISTRY:
        if mapping.technique_id.upper() == normalized:
            return mapping
    return None


def get_coverage_summary() -> dict[str, float | int]:
    """Compute detection coverage ratio for applicable techniques."""
    applicable = [t for t in TECHNIQUE_REGISTRY if t.status != "not_applicable"]
    detected = [t for t in applicable if t.status == "detected"]
    partial = [t for t in applicable if t.status == "partial"]
    blind = [t for t in TECHNIQUE_REGISTRY if t.status == "blind_spot"]

    covered = len(detected) + len(partial) * 0.5
    ratio = covered / len(applicable) if applicable else 1.0

    return {
        "total_techniques": len(TECHNIQUE_REGISTRY),
        "applicable": len(applicable),
        "detected": len(detected),
        "partial": len(partial),
        "blind_spots": len(blind),
        "coverage_ratio": round(ratio, 4),
    }


def list_blind_spots() -> list[TechniqueMapping]:
    """Return techniques marked as blind spots."""
    return [t for t in TECHNIQUE_REGISTRY if t.status == "blind_spot"]
