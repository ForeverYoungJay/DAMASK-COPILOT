"""Load-case schema models."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class LoadCaseRequest(BaseModel):
    """Simple load-case request."""

    path: Path
    strain_rate: float = Field(..., gt=0.0)
    final_strain: float = Field(..., gt=0.0)
    steps: int = Field(..., ge=1)
