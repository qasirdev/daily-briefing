"""HITL layer registry tests (Gaps #66, #95)."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.security.hitl import (
    HITL_LAYERS,
    HitlLayer,
    all_layers_operational,
    get_layer,
    layer_summary,
)


@pytest.mark.parametrize("layer", HITL_LAYERS, ids=lambda item: item.layer_id)
def test_each_hitl_layer_registered(layer: HitlLayer) -> None:
    assert layer.name
    assert layer.control
    assert layer.owner in ("human", "agent", "shared")


@pytest.mark.parametrize("layer", HITL_LAYERS, ids=lambda item: item.layer_id)
def test_implemented_layers_have_tests(layer: HitlLayer) -> None:
    if layer.status == "planned":
        pytest.skip("planned layer")
    assert layer.test_module, f"{layer.layer_id} missing test_module"
    repo_root = Path(__file__).resolve().parents[3]
    assert (repo_root / layer.test_module).is_file()


def test_eight_layers_present() -> None:
    assert len(HITL_LAYERS) == 8
    assert {layer.layer_id for layer in HITL_LAYERS} == {
        "input",
        "planning",
        "review",
        "revision",
        "execution",
        "monitoring",
        "override",
        "feedback",
    }


def test_layer_summary_counts() -> None:
    summary = layer_summary()
    assert sum(summary.values()) == 8


def test_all_layers_operational() -> None:
    assert all_layers_operational() is True


def test_get_layer_override() -> None:
    layer = get_layer("override")
    assert layer is not None
    assert layer.owner == "human"
