"""Structured LLM output schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from damask_copilot.schemas.project_plan import CandidateSimulation, EvidenceStatus


class ResearchManagerOutput(BaseModel):
    """Structured output for research-goal inference."""

    material_system: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    workflow_type: str = Field(default="simulation_run", min_length=1)
    needs_literature: bool = False
    needs_experimental_data: bool = False
    needs_damask_simulation: bool = True
    needs_parameter_optimization: bool = False
    needs_report: bool = True
    reasoning_summary: str = Field(..., min_length=1)


class MaterialKnowledgeOutput(BaseModel):
    """Structured output for material-knowledge summarization."""

    material_label: str = Field(..., min_length=1)
    crystal_structure: str = Field(..., min_length=1)
    knowledge_summary: str = Field(..., min_length=1)
    planning_considerations: list[str] = Field(default_factory=list)


class LiteratureAgentOutput(BaseModel):
    """Structured output for lightweight literature-style background notes."""

    summary: str = Field(default="")
    literature_notes: list[str] = Field(default_factory=list)
    relevant_mechanisms: list[str] = Field(default_factory=list)
    candidate_constitutive_models: list[str] = Field(default_factory=list)
    experimental_conditions: list[str] = Field(default_factory=list)
    observables_for_validation: list[str] = Field(default_factory=list)
    planning_implications: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)


class HypothesisItemOutput(BaseModel):
    """One hypothesis candidate produced by the LLM."""

    id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    evidence: list[str] = Field(default_factory=list)
    required_simulation: str = Field(..., min_length=1)
    expected_observable: str = Field(..., min_length=1)
    risks: list[str] = Field(default_factory=list)


class HypothesisAgentOutput(BaseModel):
    """Structured output for hypothesis generation."""

    hypotheses: list[HypothesisItemOutput] = Field(default_factory=list)


class ModelingStrategyOutput(BaseModel):
    """Structured output for selecting a modeling strategy."""

    simulation_abstraction: str = Field(..., min_length=1)
    geometry_strategy: str = Field(..., min_length=1)
    loading_proxy: str = Field(..., min_length=1)
    target_grains: int = Field(..., ge=1)
    comparison_targets: list[str] = Field(default_factory=list)
    required_outputs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    requires_human_review: bool = False


class ExperimentalDataInterpretationOutput(BaseModel):
    """Structured interpretation layered on top of deterministic experimental summaries."""

    semantic_column_guesses: dict[str, str] = Field(default_factory=dict)
    likely_observables: list[str] = Field(default_factory=list)
    metadata_questions: list[str] = Field(default_factory=list)
    interpretation_summary: str = Field(default="")


class ParameterAssessmentOutput(BaseModel):
    """Structured interpretation of parameter suitability for the current study."""

    suitability_summary: str = Field(default="")
    likely_mismatches: list[str] = Field(default_factory=list)
    assumption_risks: list[str] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)
    requires_human_review: bool = False


class AlignmentInterpretationOutput(BaseModel):
    """Structured interpretation of experiment-simulation agreement or mismatch."""

    summary: str = Field(default="")
    likely_mismatch_causes: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    confidence: str = Field(default="low")


class SimulationPlannerOutput(BaseModel):
    """Structured output for simulation planning."""

    plan_name: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    grid_type: str = Field(..., min_length=1)
    cells: list[int] = Field(..., min_length=3)
    size: list[float] = Field(..., min_length=3)
    grains: int = Field(..., ge=1)
    loading_mode: str = Field(..., min_length=1)
    loading_direction: str = Field(..., min_length=1)
    final_strain: float = Field(..., gt=0.0)
    strain_rate: float = Field(..., gt=0.0)
    steps: int = Field(..., ge=1)
    outputs: list[str] = Field(default_factory=list)


class ScientificCriticOutput(BaseModel):
    """Structured output for scientific critique."""

    summary: str = Field(..., min_length=1)
    strengths: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)


class IterationDecisionOutput(BaseModel):
    """Structured output for deciding whether to continue research iterations."""

    action: str = Field(default="finish")
    continue_research: bool = False
    rationale: str = Field(..., min_length=1)
    next_focus: str | None = None


class ReportWriterOutput(BaseModel):
    """Structured output for the final report framing."""

    title: str = Field(..., min_length=1)
    executive_summary: str = Field(..., min_length=1)
    key_points: list[str] = Field(default_factory=list)
    next_recommended_simulations: list[str] = Field(default_factory=list)


class ProjectPlannerHypothesisOutput(BaseModel):
    """One project-level hypothesis proposed by the LLM planner."""

    id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    evidence: list[str] = Field(default_factory=list)
    validation_metric: str = Field(..., min_length=1)
    type: str = Field(default="scientific_hypothesis", min_length=1)


class ProjectPlannerOutput(BaseModel):
    """Structured output for the v1 ProjectPlannerAgent."""

    project_objective: str = Field(..., min_length=1)
    research_questions: list[str] = Field(default_factory=list)
    hypotheses: list[ProjectPlannerHypothesisOutput] = Field(default_factory=list)
    evidence_status: list[EvidenceStatus] = Field(default_factory=list)
    validation_metrics: list[str] = Field(default_factory=list)
    calibration_strategy: dict[str, object] = Field(default_factory=dict)
    candidate_simulations: list[CandidateSimulation] = Field(default_factory=list)
    stopping_criteria: list[str] = Field(default_factory=list)
    iteration_logic: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(default_factory=list)
    next_action: str = Field(default="simulation_designer", min_length=1)
