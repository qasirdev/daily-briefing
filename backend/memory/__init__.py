"""CoALA memory layers — Working, Semantic, Procedural, and Episodic."""

from backend.memory.audit import (
    MemoryAuditTrail,
    MemoryMutationAuditEntry,
    MemoryReadAuditEntry,
    memory_audit_trail,
)
from backend.memory.consolidation import (
    consolidate_semantic_memory,
    distill_working_snippets,
    distill_working_to_episodic,
)
from backend.memory.episodic import EpisodicLessonRecord, EpisodicMemoryStore
from backend.memory.ingestion import (
    IngestionValidationResult,
    SemanticIngestionRejected,
    SourceTrust,
    compute_content_hash,
    validate_semantic_content,
)
from backend.memory.privilege import sanitize_lesson_content
from backend.memory.procedural import (
    ProceduralMemoryStore,
    ProceduralSkillDefinition,
    ProceduralSkillRecord,
)
from backend.memory.quarantine import (
    MemoryQuarantineError,
    MemoryQuarantineResult,
    delete_memory,
    quarantine_memory,
    restore_memory,
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
    "IngestionValidationResult",
    "EpisodicLessonRecord",
    "EpisodicMemoryStore",
    "MemoryAuditTrail",
    "MemoryMutationAuditEntry",
    "MemoryQuarantineError",
    "MemoryQuarantineResult",
    "MemoryReadAuditEntry",
    "ProceduralMemoryStore",
    "ProceduralSkillDefinition",
    "ProceduralSkillRecord",
    "SemanticIngestionRejected",
    "SemanticMemoryRecord",
    "SemanticMemoryStore",
    "SourceTrust",
    "WorkingMemoryManager",
    "WorkingMemorySnapshot",
    "build_focus_retrieval_query",
    "compute_content_hash",
    "consolidate_semantic_memory",
    "delete_memory",
    "distill_working_snippets",
    "distill_working_to_episodic",
    "format_episodic_context",
    "format_procedural_context",
    "format_semantic_context",
    "memory_audit_trail",
    "quarantine_memory",
    "restore_memory",
    "retrieve_agent_memory",
    "sanitize_lesson_content",
    "retrieve_episodic_lessons",
    "retrieve_procedural_skills",
    "retrieve_semantic_context",
    "validate_semantic_content",
]
