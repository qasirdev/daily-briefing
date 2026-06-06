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


def log_guardrail_violation(
    trace_id: str,
    agent_id: str,
    violation: GuardrailViolation,
) -> None:
    """Log guardrail violation and increment Prometheus counter for drift detection."""
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
