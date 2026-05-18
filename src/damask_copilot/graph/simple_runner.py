"""Simple deterministic graph runner."""

from __future__ import annotations

from damask_copilot.graph.research_graph import DamaskResearchGraph
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.research_state import ResearchState


def run_research_graph(
    state: ResearchState,
    *,
    use_llm: bool | None = None,
    model_name: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
) -> ResearchState:
    """Run the research graph."""
    return DamaskResearchGraph(
        use_llm=state.use_llm if use_llm is None else use_llm,
        model_name=state.model_name or model_name,
        llm_runner=llm_runner,
    ).run(state)
