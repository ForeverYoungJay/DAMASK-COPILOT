"""Material schema models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel


class MaterialYamlRequest(BaseModel):
    """Simple material YAML creation request."""

    path: Path
    material_name: str
    phase_name: str
    lattice: str
    elastic: dict[str, Any]
    plastic: dict[str, Any] | None = None
