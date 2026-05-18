"""Research goal schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResearchGoal(BaseModel):
    """A coarse research goal inferred from a user query."""

    user_query: str = Field(..., min_length=1)
    material_system: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
