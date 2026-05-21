"""Agent implementations for DAMASK Copilot.

Preferred v1 agents:
- ResearchManagerAgent
- ScientificKnowledgeAgent
- ProjectPlannerAgent
- SimulationDesignerAgent
- DAMASKExecutionAgent
- AnalysisAndCriticAgent
- ResearchReportAgent

Older micro-agents remain importable as deprecated compatibility wrappers.
"""

from damask_copilot.agents.base import BaseAgent
from damask_copilot.agents.approval_gate import ApprovalGateAgent
from damask_copilot.agents.analysis_critic import AnalysisAndCriticAgent
from damask_copilot.agents.damask_input_builder import DAMASKInputBuilderAgent
from damask_copilot.agents.damask_execution import DAMASKExecutionAgent
from damask_copilot.agents.experiment_simulation_alignment import ExperimentSimulationAlignmentAgent
from damask_copilot.agents.experimental_data_agent import ExperimentalDataAgent
from damask_copilot.agents.human_review_agent import HumanReviewAgent
from damask_copilot.agents.hypothesis_agent import HypothesisAgent
from damask_copilot.agents.iteration_decider import IterationDeciderAgent
from damask_copilot.agents.iteration_decision import IterationDecisionAgent
from damask_copilot.agents.literature_agent import LiteratureAgent
from damask_copilot.agents.material_knowledge import MaterialKnowledgeAgent
from damask_copilot.agents.modeling_strategy_agent import ModelingStrategyAgent
from damask_copilot.agents.parameter_agent import ParameterAgent
from damask_copilot.agents.parameter_database import ParameterDatabaseAgent
from damask_copilot.agents.postprocessor import PostProcessingAgent
from damask_copilot.agents.project_planner import ProjectPlannerAgent
from damask_copilot.agents.report_writer import ReportWriterAgent
from damask_copilot.agents.research_manager import ResearchManagerAgent
from damask_copilot.agents.research_project_planner import ResearchProjectPlannerAgent
from damask_copilot.agents.research_report import ResearchReportAgent
from damask_copilot.agents.scientific_knowledge import ScientificKnowledgeAgent
from damask_copilot.agents.scientific_critic import ScientificCriticAgent
from damask_copilot.agents.simulation_checker import SimulationCheckerAgent
from damask_copilot.agents.simulation_designer import SimulationDesignerAgent
from damask_copilot.agents.simulation_planner import SimulationPlannerAgent
from damask_copilot.agents.simulation_runner import SimulationRunnerAgent

__all__ = [
    "BaseAgent",
    "ApprovalGateAgent",
    "AnalysisAndCriticAgent",
    "DAMASKInputBuilderAgent",
    "DAMASKExecutionAgent",
    "ExperimentSimulationAlignmentAgent",
    "ExperimentalDataAgent",
    "HumanReviewAgent",
    "HypothesisAgent",
    "IterationDeciderAgent",
    "IterationDecisionAgent",
    "LiteratureAgent",
    "MaterialKnowledgeAgent",
    "ModelingStrategyAgent",
    "ParameterAgent",
    "ParameterDatabaseAgent",
    "PostProcessingAgent",
    "ProjectPlannerAgent",
    "ReportWriterAgent",
    "ResearchManagerAgent",
    "ResearchProjectPlannerAgent",
    "ResearchReportAgent",
    "ScientificKnowledgeAgent",
    "ScientificCriticAgent",
    "SimulationCheckerAgent",
    "SimulationDesignerAgent",
    "SimulationPlannerAgent",
    "SimulationRunnerAgent",
]
