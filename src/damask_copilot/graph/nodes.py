"""LangGraph node factories for DAMASK Copilot."""

from __future__ import annotations

from typing import Any, Callable

from damask_copilot.agents.approval_gate import ApprovalGateAgent
from damask_copilot.agents.damask_input_builder import DAMASKInputBuilderAgent
from damask_copilot.agents.iteration_decider import IterationDeciderAgent
from damask_copilot.agents.literature_agent import LiteratureAgent
from damask_copilot.agents.material_knowledge import MaterialKnowledgeAgent
from damask_copilot.agents.parameter_database import ParameterDatabaseAgent
from damask_copilot.agents.postprocessor import PostProcessingAgent
from damask_copilot.agents.report_writer import ReportWriterAgent
from damask_copilot.agents.research_manager import ResearchManagerAgent
from damask_copilot.agents.scientific_critic import ScientificCriticAgent
from damask_copilot.agents.simulation_checker import SimulationCheckerAgent
from damask_copilot.agents.simulation_planner import SimulationPlannerAgent
from damask_copilot.agents.simulation_runner import SimulationRunnerAgent
from damask_copilot.graph.state import (
    DamaskResearchState,
    append_error,
    append_trace,
    graph_state_from_legacy,
    legacy_state_from_graph,
)
from damask_copilot.llm.structured_runner import StructuredLLMRunner


def build_default_nodes(
    *,
    use_llm: bool = False,
    model_name: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
) -> dict[str, Any]:
    """Build the legacy deterministic research-graph node mapping."""
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
        "report_writer": ReportWriterAgent(use_llm=use_llm, model_name=model_name, llm_runner=llm_runner),
    }


def build_nodes(
    *,
    use_llm: bool = False,
    model: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
    agent_overrides: dict[str, Any] | None = None,
) -> dict[str, Callable[[DamaskResearchState], DamaskResearchState]]:
    """Build node callables for the research graph."""
    overrides = agent_overrides or {}
    agents = {
        "research_manager": overrides.get("research_manager")
        or ResearchManagerAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
        "literature_agent": overrides.get("literature_agent")
        or LiteratureAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
        "material_knowledge": overrides.get("material_knowledge")
        or MaterialKnowledgeAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
        "parameter_database": overrides.get("parameter_database") or ParameterDatabaseAgent(),
        "simulation_planner": overrides.get("simulation_planner")
        or SimulationPlannerAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
        "damask_input_builder": overrides.get("damask_input_builder") or DAMASKInputBuilderAgent(),
        "simulation_checker": overrides.get("simulation_checker") or SimulationCheckerAgent(),
        "approval_gate": overrides.get("approval_gate") or ApprovalGateAgent(),
        "simulation_runner": overrides.get("simulation_runner") or SimulationRunnerAgent(),
        "postprocessor": overrides.get("postprocessor") or PostProcessingAgent(),
        "scientific_critic": overrides.get("scientific_critic")
        or ScientificCriticAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
        "iteration_decider": overrides.get("iteration_decider")
        or IterationDeciderAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
        "report_writer": overrides.get("report_writer")
        or ReportWriterAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
    }

    return {
        "research_manager": _legacy_node("research_manager", agents["research_manager"]),
        "literature_agent": _direct_node("literature_agent", agents["literature_agent"]),
        "material_knowledge": _legacy_node("material_knowledge", agents["material_knowledge"]),
        "parameter_database": _legacy_node("parameter_database", agents["parameter_database"]),
        "simulation_planner": _legacy_node("simulation_planner", agents["simulation_planner"]),
        "damask_input_builder": _legacy_node("damask_input_builder", agents["damask_input_builder"]),
        "simulation_checker": _legacy_node("simulation_checker", agents["simulation_checker"]),
        "approval_gate": _direct_node("approval_gate", agents["approval_gate"]),
        "simulation_runner": _legacy_node("simulation_runner", agents["simulation_runner"]),
        "postprocessor": _legacy_node("postprocessor", agents["postprocessor"]),
        "scientific_critic": _legacy_node("scientific_critic", agents["scientific_critic"]),
        "iteration_decider": _iteration_node(agents["iteration_decider"]),
        "report_writer": _legacy_node("report_writer", agents["report_writer"]),
    }


def _legacy_node(name: str, agent) -> Callable[[DamaskResearchState], DamaskResearchState]:
    def _node(state: DamaskResearchState) -> DamaskResearchState:
        try:
            legacy_state = legacy_state_from_graph(state)
            updated_legacy = agent.run(legacy_state)
            return graph_state_from_legacy(state, updated_legacy)
        except Exception as exc:
            errored = append_error(state, f"{name}: {type(exc).__name__}: {exc}")
            return append_trace(errored, name, "error", {"error": f"{type(exc).__name__}: {exc}"})

    return _node


def _direct_node(name: str, agent) -> Callable[[DamaskResearchState], DamaskResearchState]:
    def _node(state: DamaskResearchState) -> DamaskResearchState:
        try:
            return agent.run(state)
        except Exception as exc:
            errored = append_error(state, f"{name}: {type(exc).__name__}: {exc}")
            return append_trace(errored, name, "error", {"error": f"{type(exc).__name__}: {exc}"})

    return _node


def _iteration_node(agent) -> Callable[[DamaskResearchState], DamaskResearchState]:
    def _node(state: DamaskResearchState) -> DamaskResearchState:
        try:
            updated = agent.run(state)
            decision = updated.get("iteration_decision")
            should_continue = bool(getattr(decision, "continue_research", False)) if decision is not None else False
            if should_continue:
                next_state = dict(updated)
                next_state["iteration"] = next_state.get("iteration", 0) + 1
                return next_state
            return updated
        except Exception as exc:
            errored = append_error(state, f"iteration_decider: {type(exc).__name__}: {exc}")
            return append_trace(errored, "iteration_decider", "error", {"error": f"{type(exc).__name__}: {exc}"})

    return _node
