"""Graph node registry."""

from __future__ import annotations

from damask_copilot.agents.damask_input_builder import DAMASKInputBuilderAgent
from damask_copilot.agents.material_knowledge import MaterialKnowledgeAgent
from damask_copilot.agents.parameter_database import ParameterDatabaseAgent
from damask_copilot.agents.postprocessor import PostProcessingAgent
from damask_copilot.agents.report_writer import ReportWriterAgent
from damask_copilot.agents.research_manager import ResearchManagerAgent
from damask_copilot.agents.scientific_critic import ScientificCriticAgent
from damask_copilot.agents.simulation_checker import SimulationCheckerAgent
from damask_copilot.agents.simulation_planner import SimulationPlannerAgent
from damask_copilot.agents.simulation_runner import SimulationRunnerAgent
from damask_copilot.llm.structured_runner import StructuredLLMRunner


def build_default_nodes(
    *,
    use_llm: bool = False,
    model_name: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
) -> dict[str, object]:
    """Return the default node registry."""
    return {
        "research_manager": ResearchManagerAgent(use_llm=use_llm, model_name=model_name, llm_runner=llm_runner),
        "parameter_database": ParameterDatabaseAgent(),
        "material_knowledge": MaterialKnowledgeAgent(use_llm=use_llm, model_name=model_name, llm_runner=llm_runner),
        "simulation_planner": SimulationPlannerAgent(use_llm=use_llm, model_name=model_name, llm_runner=llm_runner),
        "input_builder": DAMASKInputBuilderAgent(),
        "checker": SimulationCheckerAgent(),
        "runner": SimulationRunnerAgent(),
        "postprocessor": PostProcessingAgent(),
        "scientific_critic": ScientificCriticAgent(use_llm=use_llm, model_name=model_name, llm_runner=llm_runner),
        "report_writer": ReportWriterAgent(),
    }
