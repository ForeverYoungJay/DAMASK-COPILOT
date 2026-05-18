"""Post-processing report schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PostprocessReport(BaseModel):
    """Status of post-processing for a research run."""

    ok: bool
    skipped: bool
    result_file: str
    derived_files: list[str] = Field(default_factory=list)
    summary: str
