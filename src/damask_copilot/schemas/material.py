"""Material-related schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MaterialParameterCard(BaseModel):
    """Material parameters selected for a research run."""

    material_id: str = Field(..., min_length=1)
    material_name: str = Field(..., min_length=1)
    crystal_structure: str = Field(..., min_length=1)
    phase_type: str = Field(..., min_length=1)
    source_path: str = Field(..., min_length=1)
    confidence: str = Field(default="medium", min_length=1)
    explicit_assumptions: list[str] = Field(default_factory=list)
    is_demo_template: bool = False
    parameters: dict[str, Any] = Field(default_factory=dict)
