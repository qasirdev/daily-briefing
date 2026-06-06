"""CoALA memory layers — Working, Semantic, Procedural, and Episodic."""

from backend.memory.audit import MemoryAuditTrail, MemoryReadAuditEntry, memory_audit_trail
from backend.memory.consolidation import (
    consolidate_semantic_memory,
    distill_working_snippets,
    distill_working_to_episodic,
)
from backend.memory.episodic import EpisodicLessonRecord, EpisodicMemoryStore
from backend.memory.procedural import (
    ProceduralMemoryStore,
    ProceduralSkillDefinition,
    ProceduralSkillRecord,
)
from backend.memory.retrieval import (
    AgentMemoryContext,
    build_focus_retrieval_query,
    format_episodic_context,
    format_procedural_context,
    format_semantic_context,
    retrieve_agent_memory,
    retrieve_episodic_lessons,
    retrieve_procedural_skills,
    retrieve_semantic_context,
)
from backend.memory.semantic import SemanticMemoryRecord, SemanticMemoryStore
from backend.memory.working import WorkingMemoryManager, WorkingMemorySnapshot

__all__ = [
    "AgentMemoryContext",
    "EpisodicLessonRecord",
    "EpisodicMemoryStore",
    "MemoryAuditTrail",
    "MemoryReadAuditEntry",
    "ProceduralMemoryStore",
    "ProceduralSkillDefinition",
    "ProceduralSkillRecord",
    "SemanticMemoryRecord",
    "SemanticMemoryStore",
    "WorkingMemoryManager",
    "WorkingMemorySnapshot",
    "build_focus_retrieval_query",
    "consolidate_semantic_memory",
    "distill_working_snippets",
    "distill_working_to_episodic",
    "format_episodic_context",
    "format_procedural_context",
    "format_semantic_context",
    "memory_audit_trail",
    "retrieve_agent_memory",
    "retrieve_episodic_lessons",
    "retrieve_procedural_skills",
    "retrieve_semantic_context",
]
