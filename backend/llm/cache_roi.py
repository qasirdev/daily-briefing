"""Cache ROI helpers for Week 2 validation."""

from __future__ import annotations

WEEK1_BASELINE_HIT_RATE_PERCENT = 0.0


def calculate_cache_hit_rate_percent(*, hits: int, misses: int) -> float:
    """Return cache hit rate as a percentage."""
    total = hits + misses
    if total <= 0:
        return 0.0
    return hits / total * 100.0


def calculate_token_savings_percent(*, cached_tokens: int, prompt_tokens: int) -> float:
    """Return fraction of prompt tokens served from cache."""
    if prompt_tokens <= 0:
        return 0.0
    return min(cached_tokens / prompt_tokens * 100.0, 100.0)


def cache_roi_vs_week1_baseline(
    *,
    hit_rate_percent: float,
    baseline_percent: float = WEEK1_BASELINE_HIT_RATE_PERCENT,
) -> float:
    """Return hit-rate improvement over the Week 1 baseline (no caching)."""
    return hit_rate_percent - baseline_percent


def warm_path_meets_target(*, hits: int, misses: int, target_percent: float = 70.0) -> bool:
    """Return True when warm-path cache hit rate meets the Week 2 target."""
    return calculate_cache_hit_rate_percent(hits=hits, misses=misses) >= target_percent
