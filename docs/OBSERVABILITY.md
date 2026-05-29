# Observability & Tracing — AI Daily Briefing Assistant

**Version:** 1.5.0 | **Last Updated:** May 2026

---

## Overview

The AI Daily Briefing Assistant implements comprehensive observability using OpenTelemetry for distributed tracing, Prometheus for metrics, and structured logging for audit trails.

```
┌─────────────────────────────────────────────────────────────┐
│                     Application                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              OpenTelemetry SDK                       │    │
│  │  Traces ──────┬───────────────────────────────────   │    │
│  │  Metrics ─────┼───────────────────────────────────   │    │
│  │  Logs ────────┼───────────────────────────────────   │    │
│  └───────────────┼───────────────────────────────────┘    │
│                  │                                          │
└──────────────────┼──────────────────────────────────────────┘
                   │ OTLP (gRPC/HTTP)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenTelemetry Collector                         │
│  ┌─────────┐  ┌─────────────┐  ┌───────────────────────┐   │
│  │ Jaeger  │  │ Prometheus  │  │ Loki (optional)       │   │
│  │ (traces)│  │ (metrics)   │  │ (logs)                │   │
│  └─────────┘  └─────────────┘  └───────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Distributed Tracing

### Trace Context Propagation

Every request receives a `trace_id` that propagates through all agents and MCP calls:

```python
from opentelemetry import trace
from opentelemetry.propagate import inject, extract

tracer = trace.get_tracer("daily-briefing")

@app.post("/api/v1/briefing/generate")
async def generate_briefing(request: Request):
    with tracer.start_as_current_span("generate_briefing") as span:
        trace_id = format(span.get_span_context().trace_id, '032x')
        
        state = BriefingGraphState(
            user_id=user.id,
            request_id=str(uuid.uuid4()),
            trace_id=trace_id,
            ...
        )
        
        result = await graph.ainvoke(state)
        return result
```

### Span Hierarchy

```
generate_briefing (root span)
├── orchestrator.route
│   ├── task_agent.execute
│   │   └── mcp.postgres.query
│   ├── calendar_agent.execute
│   │   └── mcp.calendar.get_events
│   └── focus_agent.execute
│       └── llm.chat_completion
├── critic_agent.execute
│   └── llm.chat_completion
└── orchestrator.present
```

### Required Span Attributes

| Attribute | Type | Description |
|---|---|---|
| `user.id` | string | User identifier (hashed for privacy) |
| `request.id` | string | Unique request identifier |
| `agent.id` | string | Agent that created the span |
| `agent.role` | string | Canonical role (doer, planner, etc.) |
| `llm.model` | string | Model used for completion |
| `llm.tokens.input` | int | Input tokens consumed |
| `llm.tokens.output` | int | Output tokens generated |
| `mcp.server` | string | MCP server name |
| `mcp.tool` | string | MCP tool called |
| `data.classification` | string | Data classification level |

### Trace ID in AgentResultEnvelope

```json
{
  "agent_id": "focus",
  "metadata": {
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "execution_ms": 1234,
    "tokens_used": 512
  }
}
```

---

## Metrics Registry

### Application Metrics

| Metric Name | Type | Labels | Description |
|---|---|---|---|
| `briefing_generation_duration_seconds` | Histogram | `status`, `degraded` | End-to-end briefing generation time |
| `briefing_requests_total` | Counter | `status` | Total briefing requests |
| `agent_execution_duration_seconds` | Histogram | `agent_id`, `role`, `status` | Per-agent execution time |
| `agent_executions_total` | Counter | `agent_id`, `role`, `status` | Total agent executions |

### LLM Metrics

| Metric Name | Type | Labels | Description |
|---|---|---|---|
| `llm_tokens_used_total` | Counter | `agent_id`, `model`, `direction` | Tokens consumed (input/output) |
| `llm_request_duration_seconds` | Histogram | `model`, `status` | LLM API latency |
| `llm_requests_total` | Counter | `model`, `status` | Total LLM requests |
| `llm_fallback_total` | Counter | `from_model`, `to_model`, `reason` | Fallback triggers |

### MCP Metrics

| Metric Name | Type | Labels | Description |
|---|---|---|---|
| `mcp_call_duration_seconds` | Histogram | `server`, `tool`, `status` | MCP tool call latency |
| `mcp_calls_total` | Counter | `server`, `tool`, `status` | Total MCP calls |
| `mcp_errors_total` | Counter | `server`, `tool`, `error_type` | MCP errors |
| `mcp_active_connections` | Gauge | `server` | Active MCP connections |

### DLQ Metrics

| Metric Name | Type | Labels | Description |
|---|---|---|---|
| `dlq_events_total` | Counter | `reason`, `agent_id` | Dead letter queue entries |
| `dlq_retry_total` | Counter | `reason`, `success` | DLQ retry attempts |
| `dlq_queue_size` | Gauge | — | Current DLQ size |

### Security Metrics

| Metric Name | Type | Labels | Description |
|---|---|---|---|
| `security_violations_total` | Counter | `type`, `agent_id` | Security events |
| `token_budget_exceeded_total` | Counter | `agent_id` | Budget overruns |
| `consent_requests_total` | Counter | `mcp_server`, `outcome` | Consent prompts |

---

## Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'daily-briefing'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
```

### FastAPI Metrics Endpoint

```python
from prometheus_client import make_asgi_app, Counter, Histogram

# Metrics definitions
BRIEFING_DURATION = Histogram(
    'briefing_generation_duration_seconds',
    'Time to generate briefing',
    ['status', 'degraded'],
    buckets=[0.5, 1, 2, 5, 10, 30, 60]
)

AGENT_DURATION = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution time',
    ['agent_id', 'role', 'status'],
    buckets=[0.1, 0.5, 1, 2, 5, 10]
)

LLM_TOKENS = Counter(
    'llm_tokens_used_total',
    'LLM tokens consumed',
    ['agent_id', 'model', 'direction']
)

# Mount metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

---

## Frontend Observability Badge

The `<ObservabilityBadge />` component displays real-time execution metrics:

```typescript
interface ObservabilityData {
  executionMs: number;
  tokensUsed: number;
  modelUsed: string;
  status: 'success' | 'degraded' | 'failure';
  agentBreakdown: {
    agentId: string;
    executionMs: number;
    tokensUsed: number;
  }[];
}

function ObservabilityBadge({ data }: { data: ObservabilityData }) {
  return (
    <div className="flex items-center gap-4 text-sm text-gray-600">
      <span>
        <ClockIcon className="h-4 w-4 inline" />
        {data.executionMs}ms
      </span>
      <span>
        <ChipIcon className="h-4 w-4 inline" />
        {data.tokensUsed} tokens
      </span>
      <span>
        <ServerIcon className="h-4 w-4 inline" />
        {data.modelUsed}
      </span>
      {data.status === 'degraded' && (
        <span className="text-yellow-600">
          <ExclamationIcon className="h-4 w-4 inline" />
          Degraded
        </span>
      )}
    </div>
  );
}
```

---

## Dead Letter Queue (DLQ) Observability

### DLQ Event Structure

```python
class DLQEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    user_id: UUID
    agent_id: str
    reason: Literal[
        "security_violation_detected",
        "max_retries_exceeded",
        "token_budget_exceeded",
        "mcp_timeout",
        "consent_expired",
    ]
    envelope: AgentResultEnvelope
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    retried_at: datetime | None = None
    retry_count: int = 0
```

### DLQ Dashboard Queries

```sql
-- Events by reason (last 24h)
SELECT reason, COUNT(*) as count
FROM dlq_events
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY reason
ORDER BY count DESC;

-- Retry success rate
SELECT 
  reason,
  SUM(CASE WHEN retried_at IS NOT NULL THEN 1 ELSE 0 END) as retried,
  COUNT(*) as total
FROM dlq_events
GROUP BY reason;
```

---

## Service Level Objectives (SLOs)

### Availability SLO

| Metric | Target | Measurement |
|---|---|---|
| Briefing generation success rate | 99.5% | `sum(briefing_requests_total{status="success"}) / sum(briefing_requests_total)` |
| Degraded response rate | < 2% | `sum(briefing_requests_total{status="degraded"}) / sum(briefing_requests_total)` |

### Latency SLO

| Metric | Target | Measurement |
|---|---|---|
| P50 generation time | < 3s | `histogram_quantile(0.5, briefing_generation_duration_seconds)` |
| P95 generation time | < 10s | `histogram_quantile(0.95, briefing_generation_duration_seconds)` |
| P99 generation time | < 30s | `histogram_quantile(0.99, briefing_generation_duration_seconds)` |

### Error Budget

Monthly error budget: 0.5% (approximately 3.6 hours of downtime/degradation)

```promql
# Error budget remaining
1 - (
  sum(increase(briefing_requests_total{status!="success"}[30d])) /
  sum(increase(briefing_requests_total[30d]))
) / 0.005
```

---

## Alert Rules

### Critical Alerts

```yaml
# alerts.yml
groups:
  - name: daily-briefing-critical
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(briefing_requests_total{status="failure"}[5m])) /
          sum(rate(briefing_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in briefing generation"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: SecurityViolationSpike
        expr: |
          sum(increase(security_violations_total[10m])) > 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Security violation spike detected"
```

### Warning Alerts

```yaml
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, rate(briefing_generation_duration_seconds_bucket[5m])) > 15
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High P95 latency"
          
      - alert: DLQGrowing
        expr: |
          dlq_queue_size > 100
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "DLQ queue is growing"
```

---

## Structured Logging

### Log Format

```json
{
  "timestamp": "2026-05-29T14:30:00.000Z",
  "level": "info",
  "logger": "briefing.orchestrator",
  "message": "briefing_generated",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "user_id": "usr_abc123",
  "request_id": "req_xyz789",
  "execution_ms": 2345,
  "tokens_used": 1024,
  "status": "success",
  "agents_executed": ["task", "calendar", "focus", "critic"]
}
```

### Log Levels

| Level | Usage |
|---|---|
| `debug` | Detailed diagnostic information (disabled in production) |
| `info` | Normal operational events |
| `warning` | Unexpected but recoverable situations |
| `error` | Errors that prevent normal operation |
| `critical` | System-wide failures requiring immediate attention |

---

*Observability Documentation — Version 1.5.0 — May 2026*
