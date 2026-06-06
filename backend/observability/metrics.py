"""Observability metrics for AI Daily Briefing Assistant.

Defines Prometheus metrics for monitoring agent behavior, including rogue
agent drift detection (Gap #99) and prompt caching performance (v2.0.0).
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

import structlog
from prometheus_client import Counter, Gauge, Histogram

if TYPE_CHECKING:
    from backend.schemas.envelope import GuardrailViolation

logger = structlog.get_logger()

BRIEFING_GENERATION_DURATION = Histogram(
    "briefing_generation_duration_seconds",
    "End-to-end briefing generation time",
    ["status", "degraded"],
    buckets=[0.5, 1, 2, 5, 10, 30, 60],
)

AGENT_EXECUTION_DURATION = Histogram(
    "agent_execution_duration_seconds",
    "Per-agent execution time",
    ["agent_id", "role", "status"],
    buckets=[0.1, 0.5, 1, 2, 5, 10],
)

LLM_TOKENS_USED = Counter(
    "llm_tokens_used_total",
    "LLM tokens consumed",
    ["agent_id", "model", "direction"],
)

MCP_CALL_DURATION = Histogram(
    "mcp_call_duration_seconds",
    "MCP tool call latency",
    ["server", "tool", "status"],
    buckets=[0.05, 0.1, 0.5, 1, 2, 5, 10, 30],
)

DLQ_EVENTS_TOTAL = Counter(
    "dlq_events_total",
    "Dead letter queue entries",
    ["reason", "agent_id"],
)

SECURITY_VIOLATIONS_TOTAL = Counter(
    "security_violations_total",
    "Security events detected",
    ["type", "agent_id"],
)

CONSENT_REQUESTS_TOTAL = Counter(
    "consent_requests_total",
    "Consent prompt outcomes",
    ["mcp_server", "outcome"],
)

LLM_FALLBACK_TOTAL = Counter(
    "llm_fallback_total",
    "LLM fallback triggers",
    ["from_model", "to_model", "reason"],
)

TOKEN_BUDGET_UTILIZATION = Gauge(
    "token_budget_utilization",
    "Fraction of per-agent token budget consumed",
    ["agent_id"],
)

GUARDRAIL_VIOLATIONS = Counter(
    "guardrail_violations_total",
    "Guardrail violations by agent and type for drift detection",
    ["agent_id", "violation_type", "severity"],
)

CACHE_HIT_RATE = Gauge(
    "llm_cache_hit_rate",
    "Percentage of LLM requests served from cache",
    ["provider", "model"],
)

CACHE_MISS_TOTAL = Counter(
    "llm_cache_miss_total",
    "Total cache misses requiring full LLM calls",
    ["provider", "model"],
)

CACHE_HIT_TOTAL = Counter(
    "llm_cache_hit_total",
    "Total cache hits avoiding LLM calls",
    ["provider", "model"],
)

CACHE_SIZE_BYTES = Gauge(
    "llm_cache_size_bytes",
    "Current cache size in bytes",
    ["provider"],
)

WORKING_MEMORY_UTILIZATION = Gauge(
    "working_memory_utilization",
    "Fraction of session working memory token budget consumed",
)

MEMORY_READS_TOTAL = Counter(
    "memory_reads_total",
    "Memory read operations by layer and agent",
    ["memory_layer", "agent_id"],
)

SEMANTIC_SEARCH_DURATION = Histogram(
    "semantic_search_duration_ms",
    "Semantic memory vector search latency in milliseconds",
    ["agent_id"],
    buckets=[1, 5, 10, 25, 50, 100, 250, 500],
)

EMBEDDING_REQUESTS_TOTAL = Counter(
    "embedding_requests_total",
    "Embedding API requests by provider, model, and status",
    ["provider", "model", "status"],
)

EMBEDDING_DURATION = Histogram(
    "embedding_duration_ms",
    "Embedding API latency in milliseconds",
    ["provider", "model"],
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2500],
)

MEMORY_QUARANTINE_TOTAL = Counter(
    "memory_quarantine_total",
    "Memory quarantine workflow actions",
    ["memory_layer", "action"],
)

CONSENSUS_DISAGREEMENT_TOTAL = Counter(
    "consensus_disagreement_total",
    "Multi-agent consensus disagreements by agreement level",
    ["agreement_level"],
)

MEMORY_CONSOLIDATION_DURATION = Histogram(
    "memory_consolidation_duration_seconds",
    "Memory consolidation job latency",
    ["operation"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, 30, 60],
)

AUDIT_LOG_ENTRIES_TOTAL = Counter(
    "audit_log_entries_total",
    "Cryptographically sealed audit log entries appended",
    ["event_type"],
)

AUDIT_CHAIN_VERIFICATION_FAILURES_TOTAL = Counter(
    "audit_chain_verification_failures_total",
    "Audit hash-chain verification failures detected",
)

CREDENTIAL_ISSUANCE_TOTAL = Counter(
    "credential_issuance_total",
    "JIT credential broker issuance events",
    ["service", "intent"],
)

PER_ACTION_AUTHZ_TOTAL = Counter(
    "per_action_authz_total",
    "Per-action authorization decisions",
    ["service", "action", "outcome"],
)

CONSTITUTIONAL_VIOLATIONS_TOTAL = Counter(
    "constitutional_violations_total",
    "Constitutional classifier rule violations",
    ["rule_id", "severity"],
)

SECURITY_MITRE_DETECTION_TOTAL = Counter(
    "security_mitre_detection_total",
    "MITRE ATT&CK technique detections",
    ["technique_id", "coverage"],
)

SECURITY_MITRE_COVERAGE_RATIO = Gauge(
    "security_mitre_coverage_ratio",
    "Ratio of detected MITRE ATT&CK techniques to applicable techniques",
)

LONG_TERM_DRIFT_RATIO = Gauge(
    "long_term_drift_ratio",
    "7d vs 30d guardrail violation rate ratio per agent",
    ["agent_id"],
)

SECURITY_DWELL_TIME_SECONDS = Histogram(
    "security_dwell_time_seconds",
    "Time from security incident to alert awareness",
    ["alert_type", "severity"],
    buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 86400],
)

SECURITY_ALERTS_TOTAL = Counter(
    "security_alerts_total",
    "Security alerts fired by type and severity",
    ["alert_type", "severity"],
)

SECURITY_ALERTS_INVESTIGATED_TOTAL = Counter(
    "security_alerts_investigated_total",
    "Security alerts marked as investigated",
    ["alert_type", "severity"],
)

SECURITY_ALERT_INVESTIGATION_COVERAGE = Gauge(
    "security_alert_investigation_coverage",
    "Fraction of security alerts investigated (target >0.95)",
)

AGENTIC_RAG_DECISIONS_TOTAL = Counter(
    "agentic_rag_decisions_total",
    "Agentic RAG retrieval decisions by kind and layer",
    ["decision", "layer"],
)

CONTEXT_COMPRESSION_BYTES_SAVED_TOTAL = Counter(
    "context_compression_bytes_saved_total",
    "Bytes removed by memory context compression",
)

SECURITY_ENUMERATION_ATTEMPTS_TOTAL = Counter(
    "security_enumeration_attempts_total",
    "Suspected account enumeration probe events",
    ["probe_type", "outcome"],
)


@contextmanager
def observe_agent_execution(
    *,
    agent_id: str,
    role: str,
    status: str = "success",
) -> Iterator[None]:
    """Observe per-agent execution duration and record success or failure."""
    start = time.perf_counter()
    final_status = status
    try:
        yield
    except Exception:
        final_status = "failure"
        raise
    finally:
        AGENT_EXECUTION_DURATION.labels(
            agent_id=agent_id,
            role=role,
            status=final_status,
        ).observe(time.perf_counter() - start)


@contextmanager
def observe_mcp_call(*, server: str, tool: str) -> Iterator[None]:
    """Observe MCP tool call latency and record success or failure."""
    start = time.perf_counter()
    status = "success"
    try:
        yield
    except Exception:
        status = "failure"
        raise
    finally:
        MCP_CALL_DURATION.labels(server=server, tool=tool, status=status).observe(
            time.perf_counter() - start,
        )


def record_llm_tokens(*, agent_id: str, model: str, tokens: int, direction: str = "total") -> None:
    """Increment LLM token counter when tokens were consumed."""
    if tokens <= 0:
        return
    LLM_TOKENS_USED.labels(agent_id=agent_id, model=model, direction=direction).inc(tokens)


def record_dlq_event(*, reason: str, agent_id: str) -> None:
    """Increment dead letter queue event counter."""
    DLQ_EVENTS_TOTAL.labels(reason=reason, agent_id=agent_id).inc()


def record_security_violation(*, violation_type: str, agent_id: str) -> None:
    """Increment security violation counter."""
    SECURITY_VIOLATIONS_TOTAL.labels(type=violation_type, agent_id=agent_id).inc()


def record_briefing_generation(*, status: str, degraded: bool, duration_seconds: float) -> None:
    """Record end-to-end briefing generation duration."""
    BRIEFING_GENERATION_DURATION.labels(
        status=status,
        degraded=str(degraded).lower(),
    ).observe(duration_seconds)


def record_consent_request(*, mcp_server: str, outcome: str) -> None:
    """Increment consent request outcome counter."""
    CONSENT_REQUESTS_TOTAL.labels(mcp_server=mcp_server, outcome=outcome).inc()


def record_llm_fallback(*, from_model: str, to_model: str, reason: str) -> None:
    """Increment LLM fallback counter."""
    LLM_FALLBACK_TOTAL.labels(from_model=from_model, to_model=to_model, reason=reason).inc()


def set_token_budget_utilization(*, agent_id: str, utilization: float) -> None:
    """Set per-agent token budget utilization gauge."""
    TOKEN_BUDGET_UTILIZATION.labels(agent_id=agent_id).set(min(max(utilization, 0.0), 10.0))


def record_llm_cache_usage(*, provider: str, model: str, cached_tokens: int) -> None:
    """Record prompt cache hit or miss and update hit-rate gauge."""
    if cached_tokens > 0:
        CACHE_HIT_TOTAL.labels(provider=provider, model=model).inc()
    else:
        CACHE_MISS_TOTAL.labels(provider=provider, model=model).inc()

    hits = CACHE_HIT_TOTAL.labels(provider=provider, model=model)._value.get()
    misses = CACHE_MISS_TOTAL.labels(provider=provider, model=model)._value.get()
    total = hits + misses
    if total > 0:
        CACHE_HIT_RATE.labels(provider=provider, model=model).set(hits / total * 100.0)


def set_cache_size_bytes(*, provider: str, size_bytes: int) -> None:
    """Set current cacheable prompt size gauge."""
    CACHE_SIZE_BYTES.labels(provider=provider).set(max(size_bytes, 0))


def set_working_memory_utilization(*, utilization: float) -> None:
    """Set session working memory token budget utilization gauge."""
    WORKING_MEMORY_UTILIZATION.set(min(max(utilization, 0.0), 10.0))


def record_memory_read(*, memory_layer: str, agent_id: str, count: int = 1) -> None:
    """Increment memory read counter."""
    if count <= 0:
        return
    MEMORY_READS_TOTAL.labels(memory_layer=memory_layer, agent_id=agent_id).inc(count)


def record_semantic_search_duration(*, duration_ms: float, agent_id: str) -> None:
    """Record semantic vector search latency."""
    SEMANTIC_SEARCH_DURATION.labels(agent_id=agent_id).observe(max(duration_ms, 0.0))


def record_embedding_request(
    *,
    provider: str,
    model: str,
    status: str,
    duration_ms: float,
) -> None:
    """Record embedding API usage and latency."""
    EMBEDDING_REQUESTS_TOTAL.labels(provider=provider, model=model, status=status).inc()
    if status == "success":
        EMBEDDING_DURATION.labels(provider=provider, model=model).observe(max(duration_ms, 0.0))


def record_memory_quarantine(*, memory_layer: str, action: str) -> None:
    """Increment memory quarantine workflow counter."""
    MEMORY_QUARANTINE_TOTAL.labels(memory_layer=memory_layer, action=action).inc()


def record_consensus_disagreement(*, agreement_level: str) -> None:
    """Increment consensus disagreement counter."""
    CONSENSUS_DISAGREEMENT_TOTAL.labels(agreement_level=agreement_level).inc()


def record_memory_consolidation_duration(*, operation: str, duration_seconds: float) -> None:
    """Record memory consolidation job latency."""
    MEMORY_CONSOLIDATION_DURATION.labels(operation=operation).observe(max(duration_seconds, 0.0))


def record_audit_log_entry(*, event_type: str) -> None:
    """Increment sealed audit log entry counter."""
    AUDIT_LOG_ENTRIES_TOTAL.labels(event_type=event_type).inc()


def record_audit_chain_verification_failure() -> None:
    """Increment audit chain tamper detection counter."""
    AUDIT_CHAIN_VERIFICATION_FAILURES_TOTAL.inc()


def record_credential_issuance(*, service: str, intent: str) -> None:
    """Increment JIT credential issuance counter."""
    CREDENTIAL_ISSUANCE_TOTAL.labels(service=service, intent=intent).inc()


def record_per_action_authz(*, service: str, action: str, outcome: str) -> None:
    """Increment per-action authorization counter."""
    PER_ACTION_AUTHZ_TOTAL.labels(service=service, action=action, outcome=outcome).inc()


def record_constitutional_violation(*, rule_id: str, severity: str) -> None:
    """Increment constitutional classifier violation counter."""
    CONSTITUTIONAL_VIOLATIONS_TOTAL.labels(rule_id=rule_id, severity=severity).inc()


def record_mitre_detection(*, technique_id: str, coverage: str = "detected") -> None:
    """Increment MITRE ATT&CK technique detection counter."""
    SECURITY_MITRE_DETECTION_TOTAL.labels(
        technique_id=technique_id,
        coverage=coverage,
    ).inc()


def set_mitre_coverage_ratio(*, ratio: float) -> None:
    """Set MITRE ATT&CK coverage ratio gauge."""
    SECURITY_MITRE_COVERAGE_RATIO.set(min(max(ratio, 0.0), 1.0))


def set_long_term_drift_ratio(*, agent_id: str, ratio: float) -> None:
    """Set long-term drift ratio gauge for an agent."""
    LONG_TERM_DRIFT_RATIO.labels(agent_id=agent_id).set(max(ratio, 0.0))


def record_security_dwell_time(
    *,
    alert_type: str,
    severity: str,
    dwell_seconds: float,
) -> None:
    """Record dwell time from incident to alert."""
    SECURITY_DWELL_TIME_SECONDS.labels(
        alert_type=alert_type,
        severity=severity,
    ).observe(max(dwell_seconds, 0.0))


def record_security_alert_metric(*, alert_type: str, severity: str) -> None:
    """Increment security alert counter."""
    SECURITY_ALERTS_TOTAL.labels(alert_type=alert_type, severity=severity).inc()


def record_alert_investigated_metric(*, alert_type: str, severity: str) -> None:
    """Increment investigated alert counter and update coverage gauge."""
    SECURITY_ALERTS_INVESTIGATED_TOTAL.labels(
        alert_type=alert_type,
        severity=severity,
    ).inc()
    from backend.observability.drift_monitor import get_alert_investigation_coverage

    SECURITY_ALERT_INVESTIGATION_COVERAGE.set(get_alert_investigation_coverage())


def record_agentic_rag_decision(*, decision: str, layer: str) -> None:
    """Record an agentic RAG retrieval decision."""
    AGENTIC_RAG_DECISIONS_TOTAL.labels(decision=decision, layer=layer).inc()


def record_context_compression(*, bytes_saved: int) -> None:
    """Record bytes saved by context compression."""
    if bytes_saved > 0:
        CONTEXT_COMPRESSION_BYTES_SAVED_TOTAL.inc(bytes_saved)


def record_enumeration_attempt(*, probe_type: str, outcome: str) -> None:
    """Record a suspected enumeration probe."""
    SECURITY_ENUMERATION_ATTEMPTS_TOTAL.labels(probe_type=probe_type, outcome=outcome).inc()


def log_guardrail_violation(
    trace_id: str,
    agent_id: str,
    violation: GuardrailViolation,
) -> None:
    """Log guardrail violation and increment Prometheus counter for drift detection."""
    from backend.observability.drift_monitor import (
        get_long_term_drift_ratio,
        is_long_term_drift_alert,
        record_agent_violation,
        record_security_alert,
        record_security_incident,
    )

    logger.warning(
        "guardrail_violation_detected",
        trace_id=trace_id,
        agent_id=agent_id,
        violation_type=violation.violation_type,
        severity=violation.severity,
        confidence=violation.confidence,
        matched_pattern=violation.matched_pattern,
        owasp_id="agent_10",
    )

    GUARDRAIL_VIOLATIONS.labels(
        agent_id=agent_id,
        violation_type=violation.violation_type,
        severity=violation.severity,
    ).inc()

    record_agent_violation(agent_id=agent_id, window="7d")
    record_agent_violation(agent_id=agent_id, window="30d")
    drift_ratio = get_long_term_drift_ratio(agent_id=agent_id)
    set_long_term_drift_ratio(agent_id=agent_id, ratio=drift_ratio)

    incident_id = f"{trace_id}:{violation.violation_type}"
    record_security_incident(incident_id=incident_id)

    if is_long_term_drift_alert(agent_id=agent_id):
        dwell = record_security_alert(
            alert_type="long_term_drift",
            severity="critical",
            incident_id=incident_id,
        )
        record_security_alert_metric(alert_type="long_term_drift", severity="critical")
        if dwell is not None:
            record_security_dwell_time(
                alert_type="long_term_drift",
                severity="critical",
                dwell_seconds=dwell,
            )
