from damask_copilot.agents.analysis_critic import AnalysisAndCriticAgent
from damask_copilot.agents.damask_execution import DAMASKExecutionAgent
from damask_copilot.agents.project_planner import ProjectPlannerAgent
from damask_copilot.agents.research_manager import ResearchManagerAgent
from damask_copilot.agents.research_report import ResearchReportAgent
from damask_copilot.agents.scientific_knowledge import ScientificKnowledgeAgent
from damask_copilot.agents.simulation_designer import SimulationDesignerAgent
from damask_copilot.graph.workflow import damask_copilot_workflow, run_workflow


def test_v1_agent_imports():
    assert ResearchManagerAgent is not None
    assert ScientificKnowledgeAgent is not None
    assert ProjectPlannerAgent is not None
    assert SimulationDesignerAgent is not None
    assert DAMASKExecutionAgent is not None
    assert AnalysisAndCriticAgent is not None
    assert ResearchReportAgent is not None


def test_v1_workflow_imports():
    assert damask_copilot_workflow is not None
    assert run_workflow is not None
