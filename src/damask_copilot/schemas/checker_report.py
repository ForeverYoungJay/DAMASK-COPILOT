"""Checker report schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckerReport(BaseModel):
    """Validation report produced by the checker agent."""

    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    missing_files: list[str] = Field(default_factory=list)
    checked_paths: list[str] = Field(default_factory=list)
