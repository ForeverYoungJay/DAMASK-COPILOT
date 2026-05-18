"""Simulation planning schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GeometrySpec(BaseModel):
    """Geometry specification for a DAMASK run."""

    grid_type: str = Field(..., min_length=1)
    cells: list[int] = Field(default_factory=lambda: [8, 8, 8])
    size: list[float] = Field(default_factory=lambda: [1.0, 1.0, 1.0])
    grains: int = Field(default=1, ge=1)


class LoadingSpec(BaseModel):
    """Loading specification for a DAMASK run."""

    mode: str = Field(..., min_length=1)
    direction: str = Field(default="x", min_length=1)
    final_strain: float = Field(..., gt=0.0)
    strain_rate: float = Field(..., gt=0.0)
    steps: int = Field(..., ge=1)


class SimulationPlan(BaseModel):
    """Full simulation plan produced by the planner agent."""

    name: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    workspace: str = Field(..., min_length=1)
    material_id: str = Field(..., min_length=1)
    outputs: list[str] = Field(default_factory=list)
    geometry: GeometrySpec
    loading: LoadingSpec
