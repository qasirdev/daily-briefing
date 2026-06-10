"""AI Bill of Materials (AI-BOM) loader and validation (Gap #115)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

from backend.settings import Settings, get_settings

DEFAULT_BOM_PATH = Path(__file__).resolve().parents[2] / "infrastructure" / "ai-bom.yaml"
BOM_STALE_DAYS = 7


class BomValidationError(Exception):
    """Raised when AI-BOM validation fails."""


@dataclass(frozen=True)
class BomComponent:
    """A tracked AI or library component from the BOM manifest."""

    category: str
    name: str
    version: str | None = None
    provider: str | None = None


def load_ai_bom(path: Path | None = None) -> dict[str, Any]:
    """Load and parse the AI-BOM YAML manifest."""
    bom_path = path or DEFAULT_BOM_PATH
    if not bom_path.exists():
        msg = (
            f"AI-BOM manifest missing at {bom_path}. "
            "Create infrastructure/ai-bom.yaml before running validation."
        )
        raise BomValidationError(msg)
    with bom_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        msg = f"AI-BOM at {bom_path} must be a YAML mapping"
        raise BomValidationError(msg)
    return data


def validate_bom_freshness(
    bom: dict[str, Any],
    *,
    today: date | None = None,
    stale_days: int = BOM_STALE_DAYS,
) -> list[str]:
    """Return warnings when BOM last_updated exceeds stale_days (warn-only)."""
    metadata = bom.get("metadata")
    if not isinstance(metadata, dict):
        return ["metadata.last_updated missing — cannot assess BOM freshness"]
    last_updated_raw = metadata.get("last_updated")
    if not isinstance(last_updated_raw, str):
        return ["metadata.last_updated missing — cannot assess BOM freshness"]
    try:
        last_updated = date.fromisoformat(last_updated_raw)
    except ValueError:
        return [f"metadata.last_updated invalid date: {last_updated_raw!r}"]
    reference = today or datetime.now(UTC).date()
    age_days = (reference - last_updated).days
    if age_days > stale_days:
        return [
            f"AI-BOM last_updated is {age_days} days old (>{stale_days}); schedule weekly refresh",
        ]
    return []


def list_tracked_components(bom: dict[str, Any]) -> list[BomComponent]:
    """Flatten models, embeddings, libraries, and MCP servers from the BOM."""
    components: list[BomComponent] = []
    for model in bom.get("models", []):
        if isinstance(model, dict) and model.get("name"):
            components.append(
                BomComponent(
                    category="model",
                    name=str(model["name"]),
                    version=str(model.get("version", "")) or None,
                    provider=str(model.get("provider", "")) or None,
                ),
            )
    for embedding in bom.get("embeddings", []):
        if isinstance(embedding, dict) and embedding.get("name"):
            components.append(
                BomComponent(
                    category="embedding",
                    name=str(embedding["name"]),
                    provider=str(embedding.get("provider", "")) or None,
                ),
            )
    for library in bom.get("libraries", []):
        if isinstance(library, dict) and library.get("name"):
            components.append(
                BomComponent(
                    category="library",
                    name=str(library["name"]),
                    version=str(library.get("version", "")) or None,
                ),
            )
    for server in bom.get("mcp_servers", []):
        if isinstance(server, dict) and server.get("name"):
            components.append(
                BomComponent(
                    category="mcp_server",
                    name=str(server["name"]),
                ),
            )
    return components


def _runtime_model_names(settings: Settings) -> set[str]:
    chain = settings.openrouter_model_chain
    names = set(chain)
    if settings.llm_primary_model.strip():
        names.add(settings.llm_primary_model.strip())
    if settings.local_llm_enabled or settings.llm_fallback_model.strip():
        names.add(settings.llm_fallback_model.strip())
    return {name for name in names if name}


def validate_bom_against_settings(
    settings: Settings | None = None,
    *,
    bom_path: Path | None = None,
) -> None:
    """Verify runtime settings are represented in the AI-BOM manifest."""
    resolved = settings or get_settings()
    bom = load_ai_bom(bom_path)
    components = list_tracked_components(bom)
    model_names = {component.name for component in components if component.category == "model"}
    embedding_names = {
        component.name for component in components if component.category == "embedding"
    }

    missing_models = _runtime_model_names(resolved) - model_names
    if missing_models:
        msg = f"AI-BOM missing runtime LLM models: {sorted(missing_models)}"
        raise BomValidationError(msg)

    embedding_name = resolved.embedding_model.strip()
    if embedding_name and embedding_name not in embedding_names:
        msg = f"AI-BOM missing embedding model: {embedding_name}"
        raise BomValidationError(msg)

    if resolved.local_llm_enabled or resolved.llm_fallback_model:
        fallback = resolved.llm_fallback_model.strip()
        if fallback and fallback not in model_names:
            msg = f"AI-BOM missing local fallback model: {fallback}"
            raise BomValidationError(msg)


def openssf_scorecard_minimum(bom: dict[str, Any]) -> float:
    """Return configured OpenSSF Scorecard minimum from BOM metadata."""
    metadata = bom.get("metadata", {})
    if not isinstance(metadata, dict):
        return 7.0
    supply_chain = metadata.get("supply_chain", {})
    if not isinstance(supply_chain, dict):
        return 7.0
    minimum = supply_chain.get("openssf_scorecard_minimum", 7.0)
    return float(minimum)
