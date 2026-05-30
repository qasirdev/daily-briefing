"""Prometheus application metrics."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager

from prometheus_client import Counter, Gauge, Histogram

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


@contextmanager
def observe_agent_execution(
    *,
    agent_id: str,
    role: str,
    status: str = "success",
) -> Iterator[None]:
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
    if tokens <= 0:
        return
    LLM_TOKENS_USED.labels(agent_id=agent_id, model=model, direction=direction).inc(tokens)


def record_dlq_event(*, reason: str, agent_id: str) -> None:
    DLQ_EVENTS_TOTAL.labels(reason=reason, agent_id=agent_id).inc()


def record_security_violation(*, violation_type: str, agent_id: str) -> None:
    SECURITY_VIOLATIONS_TOTAL.labels(type=violation_type, agent_id=agent_id).inc()


def record_briefing_generation(*, status: str, degraded: bool, duration_seconds: float) -> None:
    BRIEFING_GENERATION_DURATION.labels(
        status=status,
        degraded=str(degraded).lower(),
    ).observe(duration_seconds)


def record_consent_request(*, mcp_server: str, outcome: str) -> None:
    CONSENT_REQUESTS_TOTAL.labels(mcp_server=mcp_server, outcome=outcome).inc()


def record_llm_fallback(*, from_model: str, to_model: str, reason: str) -> None:
    LLM_FALLBACK_TOTAL.labels(from_model=from_model, to_model=to_model, reason=reason).inc()


def set_token_budget_utilization(*, agent_id: str, utilization: float) -> None:
    TOKEN_BUDGET_UTILIZATION.labels(agent_id=agent_id).set(min(max(utilization, 0.0), 10.0))
