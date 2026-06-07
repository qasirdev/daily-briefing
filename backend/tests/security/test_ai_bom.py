"""Tests for AI-BOM loader and validation (DB-121)."""

from pathlib import Path

import pytest
import yaml

from backend.security.bom import (
    BomValidationError,
    list_tracked_components,
    load_ai_bom,
    validate_bom_against_settings,
    validate_bom_freshness,
)
from backend.settings import Settings


def test_load_ai_bom_parses_manifest() -> None:
    bom = load_ai_bom()
    assert "models" in bom
    assert "embeddings" in bom
    assert "libraries" in bom


def test_list_tracked_components_includes_models_and_libraries() -> None:
    components = list_tracked_components(load_ai_bom())
    categories = {component.category for component in components}
    assert "model" in categories
    assert "embedding" in categories
    assert "library" in categories


def test_validate_bom_against_settings_passes_with_defaults() -> None:
    validate_bom_against_settings(
        Settings(
            llm_openrouter_models="openai/gpt-oss-120b:free,openai/gpt-4o-mini",
            llm_primary_model="openai/gpt-oss-120b",
        ),
    )


def test_validate_bom_fails_when_model_missing(tmp_path: Path) -> None:
    bom_path = tmp_path / "ai-bom.yaml"
    bom_path.write_text(
        yaml.dump(
            {
                "metadata": {"last_updated": "2026-06-06"},
                "models": [{"name": "other/model"}],
                "embeddings": [{"name": "openai/text-embedding-3-small"}],
            },
        ),
        encoding="utf-8",
    )
    settings = Settings(llm_primary_model="openai/gpt-4o-mini")
    with pytest.raises(BomValidationError, match="missing runtime LLM models"):
        validate_bom_against_settings(settings, bom_path=bom_path)


def test_validate_bom_freshness_warns_on_stale_manifest() -> None:
    bom = {"metadata": {"last_updated": "2020-01-01"}}
    warnings = validate_bom_freshness(bom, today=__import__("datetime").date(2026, 6, 6))
    assert warnings
    assert "stale" in warnings[0].lower() or "days old" in warnings[0]


def test_load_ai_bom_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(BomValidationError, match="AI-BOM manifest missing"):
        load_ai_bom(tmp_path / "missing.yaml")


def test_validate_bom_empty_openrouter_chain_falls_back_to_primary(tmp_path: Path) -> None:
    bom_path = tmp_path / "ai-bom.yaml"
    bom_path.write_text(
        yaml.dump(
            {
                "metadata": {"last_updated": "2026-06-06"},
                "models": [
                    {"name": "openai/gpt-4o-mini"},
                    {"name": "local/llama-3-8b"},
                ],
                "embeddings": [{"name": "openai/text-embedding-3-small"}],
            },
        ),
        encoding="utf-8",
    )
    settings = Settings(llm_openrouter_models="", llm_primary_model="openai/gpt-4o-mini")
    validate_bom_against_settings(settings, bom_path=bom_path)
