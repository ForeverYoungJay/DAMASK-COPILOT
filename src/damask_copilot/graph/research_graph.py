"""Research graph builder."""

from __future__ import annotations

from damask_copilot.graph.edges import END, START, next_node
from damask_copilot.graph.nodes import build_default_nodes
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.research_state import ResearchState


class DamaskResearchGraph:
    """Small deterministic graph wrapper with optional LangGraph integration."""

    def __init__(
        self,
        *,
        use_llm: bool = False,
        model_name: str | None = None,
        llm_runner: StructuredLLMRunner | None = None,
    ) -> None:
        self.nodes = build_default_nodes(use_llm=use_llm, model_name=model_name, llm_runner=llm_runner)

    def run(self, state: ResearchState) -> ResearchState:
        """Run the deterministic graph locally."""
        current = START
        while True:
            nxt = next_node(current, state)
            if nxt == END:
                return state
            agent = self.nodes[nxt]
            state = agent.run(state)
            current = nxt

    def build_langgraph(self):
        """Build a LangGraph graph when the dependency is installed."""
        try:
            from langgraph.graph import END as LANGGRAPH_END
            from langgraph.graph import START as LANGGRAPH_START
            from langgraph.graph import StateGraph
        except ImportError as exc:
            raise RuntimeError("LangGraph is not installed. Install the project dependencies to use it.") from exc

        graph = StateGraph(dict)
        for name, agent in self.nodes.items():
            graph.add_node(name, self._wrap_agent(agent))

        graph.add_edge(LANGGRAPH_START, "research_manager")
        graph.add_edge("research_manager", "parameter_database")
        graph.add_edge("parameter_database", "material_knowledge")
        graph.add_edge("material_knowledge", "simulation_planner")
        graph.add_edge("simulation_planner", "input_builder")
        graph.add_edge("input_builder", "checker")

        def route_after_checker(payload: dict) -> str:
            state = self._coerce_state(payload)
            if state.dry_run:
                return "report_writer"
            if state.checker_report and state.checker_report.ok:
                return "runner"
            return "report_writer"

        graph.add_conditional_edges(
            "checker",
            route_after_checker,
            {"report_writer": "report_writer", "runner": "runner"},
        )
        graph.add_edge("runner", "postprocessor")
        graph.add_edge("postprocessor", "scientific_critic")
        graph.add_edge("scientific_critic", "report_writer")
        graph.add_edge("report_writer", LANGGRAPH_END)
        return graph.compile()

    @staticmethod
    def _wrap_agent(agent):
        def _node(payload: dict) -> dict:
            state = DamaskResearchGraph._coerce_state(payload)
            updated = agent.run(state)
            return {"state": updated}

        return _node

    @staticmethod
    def _coerce_state(payload: dict) -> ResearchState:
        state = payload.get("state")
        if isinstance(state, ResearchState):
            return state
        if state is not None:
            return DamaskResearchGraph._validate_state(state)
        return DamaskResearchGraph._validate_state(payload)

    @staticmethod
    def _validate_state(payload: dict) -> ResearchState:
        validator = getattr(ResearchState, "model_validate", None)
        if validator is not None:
            return validator(payload)
        return ResearchState.parse_obj(payload)
