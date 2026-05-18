"""Geometry schema models."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class SeedRequest(BaseModel):
    """Random seed generation request."""

    count: int = Field(..., ge=1)
    size: list[float]
    seed: int = 0


class VoronoiGridRequest(BaseModel):
    """Voronoi grid creation request."""

    path: Path
    cells: list[int]
    size: list[float]
    grains: int = Field(..., ge=1)
    seed: int = 0
