"""Simulation run report schema."""

from __future__ import annotations

from pydantic import BaseModel


class RunReport(BaseModel):
    """Status of a simulation run attempt."""

    ok: bool
    skipped: bool
    dry_run: bool
    result_file: str
    message: str
