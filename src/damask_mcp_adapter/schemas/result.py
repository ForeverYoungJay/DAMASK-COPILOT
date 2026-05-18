"""Result schema models."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class ResultPathRequest(BaseModel):
    """Result file request."""

    path: Path


class Hdf5InspectRequest(BaseModel):
    """Low-level HDF5 inspection request."""

    path: Path
    max_items: int = Field(default=200, ge=1, le=2000)
