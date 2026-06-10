"""Critic agent for quality and safety review."""

from __future__ import annotations

import json
import time
from typing import Any

import structlog

from backend.graph.state import BriefingGraphState
from backend.llm.models import LLMResponse
from backend.llm.prompt_cache import build_llm_messages, resolve_model_name
from backend.llm.router import LLMError, LLMRouter
from backend.logging_config import agent_log_context
from backend.metrics import (
    observe_agent_execution,
    record_constitutional_violation,
    record_security_violation,
)
from backend.prompt_version import resolve_prompt_version
from backend.schemas.envelope import AgentResultEnvelope, EscalationPayload, ExecutionMetadata
from backend.security.external_texts import collect_external_texts
from backend.security.failure_messages import failure_message_for
from backend.security.input_scanner import InputSecurityScanner
from backend.settings import get_settings
from backend.telemetry import start_async_span

logger = structlog.get_logger()

MAX_REVISION_CYCLES = 2
_scanner = InputSecurityScanner()


def _heuristic_quality_issues(focus_result: AgentResultEnvelope | None) -> list[str]:
    if focus_result is None or focus_result.result is None:
        return ["Focus agent produced no output"]
    plan = focus_result.result.get("plan")
    if not isinstance(plan, dict):
        return ["Focus plan is not structured JSON"]
    issues: list[str] = []
    if not plan.get("summary"):
        issues.append("Focus plan missing summary")
    blocks = plan.get("time_blocks")
    if isinstance(blocks, list) and len(blocks) == 0 and not plan.get("summary"):
        issues.append("Focus plan has no time blocks or summary")
    return issues


async def _llm_quality_issues(
    focus_result: AgentResultEnvelope | None,
    llm: LLMRouter,
    *,
    trace_id: str,
) -> tuple[list[str], LLMResponse | None]:
    if focus_result is None or focus_result.result is None:
        return ["Focus agent produced no output"], None

    settings = get_settings()
    user_content = (
        "Review this focus plan JSON for coherence and safety. "
        "Return JSON matching output-schema.md (approved + issues).\n"
        f"{json.dumps(focus_result.result, ensure_ascii=True)}"
    )
    messages = build_llm_messages(
        "critic",
        user_content,
        model=resolve_model_name(llm),
        enable_caching=settings.enable_prompt_caching,
    )
    try:
        response = await llm.generate(
            messages=messages,
            trace_id=trace_id,
            agent_id="critic",
            output_budget=512,
        )
        parsed = json.loads(response.content)
    except (LLMError, json.JSONDecodeError):
        return _heuristic_quality_issues(focus_result), None

    if not isinstance(parsed, dict):
        return _heuristic_quality_issues(focus_result), response
    if parsed.get("approved") is True:
        return [], response
    issues = parsed.get("issues", [])
    if isinstance(issues, list):
        return [str(item) for item in issues if item], response
    return _heuristic_quality_issues(focus_result), response


async def critic_agent_node(
    state: BriefingGraphState,
    llm: LLMRouter | None = None,
) -> dict[str, Any]:
    """Review focus output and external data; enforce revision and security rules."""
    start = time.perf_counter()
    trace_id = state.get("trace_id", "0" * 32)
    revision_count = state.get("revision_count", 0)

    with agent_log_context(trace_id=trace_id, agent_id="critic"):
        async with start_async_span("agent.critic.execute", agent_id="critic", agent_role="critic"):
            with observe_agent_execution(agent_id="critic", role="critic"):
                external_texts = collect_external_texts(state)
                scan = _scanner.scan_many(external_texts, trace_id=trace_id)
                if scan.is_blocked:
                    if scan.layer == "constitutional" and scan.constitutional_rule:
                        record_constitutional_violation(
                            rule_id=scan.constitutional_rule,
                            severity="critical",
                        )
                    record_security_violation(
                        violation_type=scan.violation_type or "injection",
                        agent_id="critic",
                    )
                    execution_ms = int((time.perf_counter() - start) * 1000)
                    envelope = AgentResultEnvelope(
                        agent_id="critic",
                        canonical_role="critic",
                        status="escalated",
                        escalation=EscalationPayload(
                            reason="security_violation_detected",
                            target_agent="dlq_handler",
                            context=scan.violation_type or "injection_detected",
                        ),
                        metadata=ExecutionMetadata(
                            execution_ms=execution_ms,
                            tokens_used=0,
                            model_used="none",
                            prompt_version=resolve_prompt_version("critic"),
                            trace_id=trace_id,
                            data_classification="internal",
                        ),
                    )
                    return {
                        "critic_result": envelope,
                        "current_agent": "critic",
                        "status": "failure",
                        "failure_reason": "security_violation_detected",
                        "failure_message": failure_message_for(
                            "security_violation_detected",
                            source=scan.blocked_source,
                        ),
                    }

                focus_result = state.get("focus_result")
                llm_response: LLMResponse | None = None
                if llm is not None:
                    issues, llm_response = await _llm_quality_issues(
                        focus_result,
                        llm,
                        trace_id=trace_id,
                    )
                else:
                    issues = _heuristic_quality_issues(
                        focus_result if isinstance(focus_result, AgentResultEnvelope) else None,
                    )

                revision_required = len(issues) > 0 and revision_count < MAX_REVISION_CYCLES
                approved = len(issues) == 0 or revision_count >= MAX_REVISION_CYCLES

                execution_ms = int((time.perf_counter() - start) * 1000)
                envelope = AgentResultEnvelope(
                    agent_id="critic",
                    canonical_role="critic",
                    status="success",
                    result={
                        "approved": approved,
                        "revision_required": revision_required,
                        "issues": issues,
                        "review_cycle": revision_count + 1,
                    },
                    metadata=ExecutionMetadata(
                        execution_ms=execution_ms,
                        tokens_used=llm_response.tokens_used if llm_response else 0,
                        cost_usd=llm_response.cost_usd if llm_response else 0.0,
                        model_used=llm_response.model_used if llm_response else "none",
                        prompt_version=resolve_prompt_version("critic"),
                        trace_id=trace_id,
                        data_classification="internal",
                    ),
                )

                update: dict[str, Any] = {
                    "critic_result": envelope,
                    "current_agent": "critic",
                }
                if llm_response is not None:
                    update["total_tokens"] = state.get("total_tokens", 0) + llm_response.tokens_used
                if revision_required:
                    update["revision_count"] = revision_count + 1
                elif revision_count >= MAX_REVISION_CYCLES and issues:
                    update["status"] = "degraded"

                return update
