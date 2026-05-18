"""File-path schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GeneratedFiles(BaseModel):
    """Paths produced or reserved by the DAMASK input builder."""

    workspace_dir: str = Field(..., min_length=1)
    geometry_path: str = Field(..., min_length=1)
    load_path: str = Field(..., min_length=1)
    material_path: str = Field(..., min_length=1)
    research_state_path: str = Field(..., min_length=1)
    result_path: str = Field(..., min_length=1)
    report_path: str = Field(..., min_length=1)

    def required_input_paths(self) -> list[str]:
        """Return the file paths expected before execution."""
        return [self.geometry_path, self.load_path, self.material_path, self.research_state_path]
