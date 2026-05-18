"""Research state schema."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.critic_report import CriticReport
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.llm_outputs import (
    MaterialKnowledgeOutput,
    ResearchManagerOutput,
    ScientificCriticOutput,
    SimulationPlannerOutput,
)
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.postprocess_report import PostprocessReport
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.run_report import RunReport
from damask_copilot.schemas.simulation_plan import SimulationPlan


class TraceEvent(BaseModel):
    """One trace event recorded during graph execution."""

    agent: str
    event: str
    details: dict[str, Any] = Field(default_factory=dict)


class ResearchState(BaseModel):
    """State shared across the research graph."""

    user_query: str = Field(..., min_length=1)
    dry_run: bool = False
    use_llm: bool = False
    smoke_test: bool = False
    overwrite: bool = False
    allow_full_run: bool = False
    model_name: str | None = None
    status: str = "initialized"
    selected_material_key: str | None = None
    goal: ResearchGoal | None = None
    research_manager_output: ResearchManagerOutput | None = None
    material_card: MaterialParameterCard | None = None
    material_knowledge_output: MaterialKnowledgeOutput | None = None
    simulation_plan: SimulationPlan | None = None
    simulation_planner_output: SimulationPlannerOutput | None = None
    generated_files: GeneratedFiles | None = None
    checker_report: CheckerReport | None = None
    run_report: RunReport | None = None
    postprocess_report: PostprocessReport | None = None
    critic_report: CriticReport | None = None
    scientific_critic_output: ScientificCriticOutput | None = None
    notes: list[str] = Field(default_factory=list)
    traces: list[TraceEvent] = Field(default_factory=list)
    report_markdown: str | None = None
    report_path: str | None = None
