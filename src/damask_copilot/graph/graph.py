"""LangGraph builder for DAMASK Copilot."""

from __future__ import annotations

from damask_copilot.graph.checkpoints import build_checkpointer
from damask_copilot.graph.nodes import build_nodes
from damask_copilot.graph.routing import (
    route_after_approval,
    route_after_checker,
    route_after_iteration_decider,
    route_after_runner,
)
from damask_copilot.graph.state import DamaskResearchState
from damask_copilot.llm.structured_runner import StructuredLLMRunner


def build_damask_research_graph(
    checkpoint: bool = True,
    *,
    use_llm: bool = False,
    model: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
    agent_overrides: dict | None = None,
):
    """Build the primary LangGraph DAMASK research graph."""
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(DamaskResearchState)
    nodes = build_nodes(
        use_llm=use_llm,
        model=model,
        llm_runner=llm_runner,
        agent_overrides=agent_overrides,
    )
    for name, node in nodes.items():
        graph.add_node(name, node)

    graph.add_edge(START, "research_manager")
    graph.add_edge("research_manager", "literature_agent")
    graph.add_edge("literature_agent", "material_knowledge")
    graph.add_edge("material_knowledge", "parameter_database")
    graph.add_edge("parameter_database", "simulation_planner")
    graph.add_edge("simulation_planner", "damask_input_builder")
    graph.add_edge("damask_input_builder", "simulation_checker")

    graph.add_conditional_edges(
        "simulation_checker",
        route_after_checker,
        {"report_writer": "report_writer", "approval_gate": "approval_gate"},
    )
    graph.add_conditional_edges(
        "approval_gate",
        route_after_approval,
        {
            "scientific_critic": "scientific_critic",
            "simulation_runner": "simulation_runner",
            "report_writer": "report_writer",
        },
    )
    graph.add_conditional_edges(
        "simulation_runner",
        route_after_runner,
        {"postprocessor": "postprocessor", "scientific_critic": "scientific_critic"},
    )
    graph.add_edge("postprocessor", "scientific_critic")
    graph.add_edge("scientific_critic", "iteration_decider")
    graph.add_conditional_edges(
        "iteration_decider",
        route_after_iteration_decider,
        {"simulation_planner": "simulation_planner", "report_writer": "report_writer"},
    )
    graph.add_edge("report_writer", END)

    return graph.compile(checkpointer=build_checkpointer(checkpoint))
