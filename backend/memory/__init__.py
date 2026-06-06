"""CoALA memory layers — Working and Semantic memory (Week 2 Day 3+)."""

from backend.memory.audit import MemoryAuditTrail, MemoryReadAuditEntry, memory_audit_trail
from backend.memory.consolidation import consolidate_semantic_memory
from backend.memory.retrieval import (
    build_focus_retrieval_query,
    format_semantic_context,
    retrieve_semantic_context,
)
from backend.memory.semantic import SemanticMemoryRecord, SemanticMemoryStore
from backend.memory.working import WorkingMemoryManager, WorkingMemorySnapshot

__all__ = [
    "MemoryAuditTrail",
    "MemoryReadAuditEntry",
    "SemanticMemoryRecord",
    "SemanticMemoryStore",
    "WorkingMemoryManager",
    "WorkingMemorySnapshot",
    "build_focus_retrieval_query",
    "consolidate_semantic_memory",
    "format_semantic_context",
    "memory_audit_trail",
    "retrieve_semantic_context",
]
