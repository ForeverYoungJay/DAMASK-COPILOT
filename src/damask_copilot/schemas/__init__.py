"""Pydantic schemas for DAMASK Copilot."""

from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.llm_outputs import (
    AlignmentInterpretationOutput,
    ExperimentalDataInterpretationOutput,
    HypothesisAgentOutput,
    IterationDecisionOutput,
    LiteratureAgentOutput,
    MaterialKnowledgeOutput,
    ModelingStrategyOutput,
    ParameterAssessmentOutput,
    ReportWriterOutput,
    ResearchManagerOutput,
    ScientificCriticOutput,
    SimulationPlannerOutput,
)
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.project_plan import (
    CandidateSimulation,
    EvidenceStatus,
    ProjectMilestone,
    ProjectPlan,
)
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan

__all__ = [
    "CheckerReport",
    "AlignmentInterpretationOutput",
    "ExperimentalDataInterpretationOutput",
    "GeometrySpec",
    "HypothesisAgentOutput",
    "IterationDecisionOutput",
    "LoadingSpec",
    "LiteratureAgentOutput",
    "MaterialKnowledgeOutput",
    "MaterialParameterCard",
    "ModelingStrategyOutput",
    "ParameterAssessmentOutput",
    "CandidateSimulation",
    "EvidenceStatus",
    "ProjectMilestone",
    "ProjectPlan",
    "ReportWriterOutput",
    "ResearchGoal",
    "ResearchManagerOutput",
    "ResearchState",
    "ScientificCriticOutput",
    "SimulationPlan",
    "SimulationPlannerOutput",
]
