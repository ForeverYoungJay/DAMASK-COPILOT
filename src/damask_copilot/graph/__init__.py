"""Primary LangGraph research graph exports for DAMASK Copilot."""

from __future__ import annotations

from damask_copilot.graph.state import DamaskResearchState, create_initial_state

__all__ = ["DamaskResearchState", "build_damask_research_graph", "create_initial_state", "run_research_graph"]


def build_damask_research_graph(*args, **kwargs):
    """Lazily import and build the LangGraph research graph."""
    from damask_copilot.graph.graph import build_damask_research_graph as _build

    return _build(*args, **kwargs)


def run_research_graph(*args, **kwargs):
    """Lazily import and run the LangGraph research graph."""
    from damask_copilot.graph.runner import run_research_graph as _run

    return _run(*args, **kwargs)
