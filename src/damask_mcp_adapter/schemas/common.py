"""Common schema models."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class JsonPathRequest(BaseModel):
    """Common request containing a path."""

    path: Path


class MappingPathRequest(BaseModel):
    """Request for writing a mapping to a path."""

    path: Path
    data: dict[str, Any]


class CountSeedRequest(BaseModel):
    """Request with count and seed."""

    count: int = Field(..., ge=1)
    seed: int = 0
