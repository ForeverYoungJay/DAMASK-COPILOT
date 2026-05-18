"""Structured LLM output schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResearchManagerOutput(BaseModel):
    """Structured output for research-goal inference."""

    material_system: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    reasoning_summary: str = Field(..., min_length=1)


class MaterialKnowledgeOutput(BaseModel):
    """Structured output for material-knowledge summarization."""

    material_label: str = Field(..., min_length=1)
    crystal_structure: str = Field(..., min_length=1)
    knowledge_summary: str = Field(..., min_length=1)
    planning_considerations: list[str] = Field(default_factory=list)


class SimulationPlannerOutput(BaseModel):
    """Structured output for simulation planning."""

    plan_name: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    grid_type: str = Field(..., min_length=1)
    cells: list[int] = Field(..., min_length=3)
    size: list[float] = Field(..., min_length=3)
    grains: int = Field(..., ge=1)
    loading_mode: str = Field(..., min_length=1)
    loading_direction: str = Field(..., min_length=1)
    final_strain: float = Field(..., gt=0.0)
    strain_rate: float = Field(..., gt=0.0)
    steps: int = Field(..., ge=1)
    outputs: list[str] = Field(default_factory=list)


class ScientificCriticOutput(BaseModel):
    """Structured output for scientific critique."""

    summary: str = Field(..., min_length=1)
    strengths: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
