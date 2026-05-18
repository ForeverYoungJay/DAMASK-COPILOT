"""Checkpoint helpers for LangGraph."""

from __future__ import annotations

from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.critic_report import CriticReport
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.llm_outputs import (
    IterationDecisionOutput,
    LiteratureAgentOutput,
    MaterialKnowledgeOutput,
    ReportWriterOutput,
    ResearchManagerOutput,
    ScientificCriticOutput,
    SimulationPlannerOutput,
)
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.postprocess_report import PostprocessReport
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.run_report import RunReport
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


ALLOWED_MSGPACK_TYPES = (
    ResearchGoal,
    ResearchManagerOutput,
    LiteratureAgentOutput,
    MaterialKnowledgeOutput,
    SimulationPlannerOutput,
    ScientificCriticOutput,
    ReportWriterOutput,
    MaterialParameterCard,
    GeometrySpec,
    LoadingSpec,
    SimulationPlan,
    GeneratedFiles,
    CheckerReport,
    RunReport,
    PostprocessReport,
    CriticReport,
    IterationDecisionOutput,
)


def build_checkpointer(enabled: bool = True):
    """Return a MemorySaver checkpointer when enabled."""
    if not enabled:
        return None
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    return MemorySaver(serde=JsonPlusSerializer(allowed_msgpack_modules=ALLOWED_MSGPACK_TYPES))
