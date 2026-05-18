"""Simulation run report schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunReport(BaseModel):
    """Status of a simulation run attempt."""

    ok: bool
    status: str
    command: str | None = None
    returncode: int | None = None
    stdout_tail: list[str] = Field(default_factory=list)
    stderr_tail: list[str] = Field(default_factory=list)
    log_file: str | None = None
    result_files: list[str] = Field(default_factory=list)
    started_at: str | None = None
    finished_at: str | None = None
    message: str | None = None
