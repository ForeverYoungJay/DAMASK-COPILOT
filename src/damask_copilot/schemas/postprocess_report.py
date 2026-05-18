"""Post-processing report schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PostprocessReport(BaseModel):
    """Status of post-processing for a research run."""

    ok: bool
    status: str
    result_file: str | None = None
    inspected_fields: list[str] = Field(default_factory=list)
    stress_strain_csv: str | None = None
    vtk_dir: str | None = None
    summary: str
    warnings: list[str] = Field(default_factory=list)
