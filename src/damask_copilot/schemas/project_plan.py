"""Project-level research planning schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceStatus(BaseModel):
    """Evidence status for one project question or planning area."""

    topic: str = Field(..., min_length=1)
    status: Literal["supported", "partial", "missing", "conflicting"] = "partial"
    evidence_summary: str = Field(..., min_length=1)
    supporting_items: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ProjectMilestone(BaseModel):
    """One staged milestone in a research roadmap."""

    milestone_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    evidence_needed: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    review_required: bool = False


class CandidateSimulation(BaseModel):
    """A candidate simulation identified at project-planning level."""

    simulation_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    why_needed: str = Field(..., min_length=1)
    target_hypotheses: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    simulation_type_hint: str | None = None
    priority: int = Field(default=1, ge=1)


class ProjectPlan(BaseModel):
    """Project-level roadmap connecting evidence, milestones, and simulations."""

    project_objective: str = Field(..., min_length=1)
    research_questions: list[str] = Field(default_factory=list)
    evidence_status: list[EvidenceStatus] = Field(default_factory=list)
    milestones: list[ProjectMilestone] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    candidate_simulations: list[CandidateSimulation] = Field(default_factory=list)
    human_review_points: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    next_action: str = Field(..., min_length=1)
