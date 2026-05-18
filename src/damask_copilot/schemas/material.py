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
    parameters: dict[str, Any] = Field(default_factory=dict)
