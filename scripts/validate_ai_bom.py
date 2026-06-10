#!/usr/bin/env python3
"""Validate AI-BOM manifest against runtime settings (DB-121)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.security.bom import (  # noqa: E402
    BomValidationError,
    load_ai_bom,
    validate_bom_against_settings,
    validate_bom_freshness,
)


def main() -> int:
    bom_path = ROOT / "infrastructure" / "ai-bom.yaml"
    try:
        bom = load_ai_bom(bom_path)
        validate_bom_against_settings(bom_path=bom_path)
    except BomValidationError as exc:
        print(f"AI-BOM validation failed: {exc}", file=sys.stderr)
        return 1

    warnings = validate_bom_freshness(bom)
    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    print(f"AI-BOM validation passed: {bom_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
