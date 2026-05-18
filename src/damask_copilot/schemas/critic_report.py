"""Scientific critic report schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CriticReport(BaseModel):
    """Summary critique of the current research state."""

    summary: str
    strengths: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
