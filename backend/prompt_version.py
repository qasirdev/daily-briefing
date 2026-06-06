"""Central prompt version registry — reads CONTRACT.md per agent (Gap #136)."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import structlog

from backend.prompts_loader import PROMPTS_ROOT

logger = structlog.get_logger()

VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")
DEFAULT_VERSION = "v1.5.0"

KNOWN_AGENTS = (
    "focus",
    "critic",
    "verification",
    "adversarial",
    "task",
    "calendar",
    "orchestrator",
    "security",
)

_version_snapshot: dict[str, str] = {}


def _contract_path(agent_id: str) -> Path:
    return PROMPTS_ROOT / agent_id / "CONTRACT.md"


def parse_contract_version(agent_id: str) -> str:
    """Parse ## Version from prompts/{agent}/CONTRACT.md."""
    path = _contract_path(agent_id)
    if not path.exists():
        return DEFAULT_VERSION
    content = path.read_text(encoding="utf-8")
    in_version_section = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("## version"):
            in_version_section = True
            continue
        if in_version_section:
            if stripped.startswith("##"):
                break
            if stripped and VERSION_PATTERN.match(stripped):
                return stripped
    return DEFAULT_VERSION


@lru_cache(maxsize=32)
def resolve_prompt_version(agent_id: str) -> str:
    """Return the active prompt version for an agent."""
    return parse_contract_version(agent_id)


def list_agent_prompt_versions() -> dict[str, str]:
    """Return prompt versions for all known agents."""
    return {agent_id: resolve_prompt_version(agent_id) for agent_id in KNOWN_AGENTS}


def register_version_snapshot() -> None:
    """Capture current prompt versions for change detection."""
    global _version_snapshot
    _version_snapshot = list_agent_prompt_versions()


def detect_version_changes() -> list[tuple[str, str, str]]:
    """Return (agent_id, old_version, new_version) for changed agents."""
    current = list_agent_prompt_versions()
    changes: list[tuple[str, str, str]] = []
    for agent_id, new_version in current.items():
        old_version = _version_snapshot.get(agent_id)
        if old_version is not None and old_version != new_version:
            changes.append((agent_id, old_version, new_version))
    return changes


def check_and_invalidate_cache() -> list[tuple[str, str, str]]:
    """Detect version changes, log cache invalidation, refresh snapshot."""
    changes = detect_version_changes()
    for agent_id, old_version, new_version in changes:
        logger.info(
            "prompt_cache_version_changed",
            agent_id=agent_id,
            old_version=old_version,
            new_version=new_version,
            action="cache_invalidation_required",
        )
    register_version_snapshot()
    return changes


def clear_version_cache() -> None:
    """Clear cached version lookups (for tests)."""
    resolve_prompt_version.cache_clear()
