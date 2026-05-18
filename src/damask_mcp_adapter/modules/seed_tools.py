"""Seed generation tools mapped from DAMASK pre-processing docs."""

from __future__ import annotations

from damask_mcp_adapter.serializers import summarize_array
from damask_mcp_adapter.workspace import import_damask


def create_random_seeds(count: int, size: list[float], seed: int = 0) -> dict:
    """Create random seed points for tessellation."""
    damask = import_damask()
    seeds = damask.seeds.from_random(size, count, rng_seed=seed)
    return {
        "ok": True,
        "count": count,
        "size": size,
        "seed": seed,
        "summary": summarize_array(seeds),
    }


__all__ = ["create_random_seeds"]
