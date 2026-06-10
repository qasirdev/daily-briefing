"""Pre-focus security gate for untrusted MCP data."""

from __future__ import annotations

import time
from typing import Any

import structlog

from backend.graph.state import BriefingGraphState
from backend.kernel.security_monitor import SecurityMonitor
from backend.metrics import record_security_violation
from backend.prompt_version import resolve_prompt_version
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata
from backend.security.external_texts import collect_mcp_external_texts
from backend.security.failure_messages import failure_message_for
from backend.security.input_scanner import InputSecurityScanner

logger = structlog.get_logger()
_scanner = InputSecurityScanner()
_security_monitor = SecurityMonitor()


def _execution_metadata(
    *,
    trace_id: str,
    execution_ms: int,
) -> ExecutionMetadata:
    return ExecutionMetadata(
        execution_ms=execution_ms,
        tokens_used=0,
        model_used="none",
        prompt_version=resolve_prompt_version("critic"),
        trace_id=trace_id,
        data_classification="internal",
    )


async def input_security_gate_node(state: BriefingGraphState) -> dict[str, Any]:
    """Scan task and calendar payloads before any LLM planning runs."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    texts = collect_mcp_external_texts(state)

    scan_result = _scanner.scan_many(texts, trace_id=trace_id)
    blocked_source = scan_result.blocked_source if scan_result.is_blocked else None

    execution_ms = int((time.perf_counter() - start) * 1000)
    metadata = _execution_metadata(trace_id=trace_id, execution_ms=execution_ms)

    if not scan_result.is_blocked:
        logger.debug("input_security_gate_passed", trace_id=trace_id, execution_ms=execution_ms)
        envelope = AgentResultEnvelope(
            agent_id="input_security_gate",
            canonical_role="supervisor",
            status="success",
            result={"passed": True, "sources_scanned": list(texts.keys())},
            metadata=metadata,
        )
        return {
            "input_security_result": envelope,
            "current_agent": "input_security_gate",
        }

    record_security_violation(
        violation_type=scan_result.violation_type or "injection",
        agent_id="input_security_gate",
    )
    _security_monitor.record_violation(agent_id="input_security_gate")
    message = failure_message_for("security_violation_detected", source=blocked_source)
    logger.warning(
        "input_security_gate_blocked",
        trace_id=trace_id,
        source=blocked_source,
        matched_pattern=scan_result.matched_pattern,
        execution_ms=execution_ms,
    )
    envelope = AgentResultEnvelope(
        agent_id="input_security_gate",
        canonical_role="supervisor",
        status="escalated",
        result={
            "blocked_source": blocked_source,
            "matched_pattern": scan_result.matched_pattern,
        },
        metadata=metadata,
        escalation=EscalationPayload(
            reason="security_violation_detected",
            target_agent="dlq_handler",
            context=scan_result.matched_pattern or blocked_source or "injection_detected",
        ),
    )
    return {
        "input_security_result": envelope,
        "current_agent": "input_security_gate",
        "failure_reason": "security_violation_detected",
        "failure_message": message,
    }
