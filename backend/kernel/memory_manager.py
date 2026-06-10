"""Four-layer memory lifecycle coordination (Gaps #8-13)."""

from __future__ import annotations

from backend.memory.consolidation import consolidate_semantic_memory, distill_working_to_episodic
from backend.memory.episodic import EpisodicMemoryStore
from backend.memory.procedural import ProceduralMemoryStore
from backend.memory.semantic import SemanticMemoryStore
from backend.memory.working import WorkingMemoryManager


class MemoryManager:
    """Facade over CoALA memory layers."""

    def __init__(self) -> None:
        self.working = WorkingMemoryManager()
        self.semantic = SemanticMemoryStore()
        self.procedural = ProceduralMemoryStore()
        self.episodic = EpisodicMemoryStore()

    async def distill_session(
        self,
        *,
        user_id: str,
        session_id: str,
        working_context: list[str] | tuple[str, ...],
    ) -> str | None:
        return await distill_working_to_episodic(
            user_id=user_id,
            session_id=session_id,
            working_context=working_context,
            store=self.episodic,
        )

    async def consolidate_semantic(self, *, user_id: str, max_age_days: int = 90) -> int:
        return await consolidate_semantic_memory(user_id=user_id, max_age_days=max_age_days)
