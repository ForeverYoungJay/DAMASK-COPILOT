"""Graph and workflow exports for DAMASK Copilot."""

from __future__ import annotations

from damask_copilot.graph.materials_research_state import MaterialsResearchState, create_initial_materials_state
from damask_copilot.graph.state import DamaskResearchState, ResearchState, create_initial_state, create_v1_state

__all__ = [
    "DamaskResearchState",
    "MaterialsResearchState",
    "ResearchState",
    "build_damask_research_graph",
    "build_materials_research_graph",
    "create_initial_state",
    "create_initial_materials_state",
    "create_v1_state",
    "damask_copilot_workflow",
    "run_research_graph",
    "run_materials_research_graph",
    "run_workflow",
]


def build_damask_research_graph(*args, **kwargs):
    """Lazily import and build the LangGraph research graph."""
    from damask_copilot.graph.graph import build_damask_research_graph as _build

    return _build(*args, **kwargs)


def run_research_graph(*args, **kwargs):
    """Lazily import and run the LangGraph research graph."""
    from damask_copilot.graph.runner import run_research_graph as _run

    return _run(*args, **kwargs)


def build_materials_research_graph(*args, **kwargs):
    """Lazily import and build the generic materials research graph."""
    from damask_copilot.graph.materials_research_graph import build_materials_research_graph as _build

    return _build(*args, **kwargs)


def run_materials_research_graph(*args, **kwargs):
    """Lazily import and run the generic materials research graph."""
    from damask_copilot.graph.materials_research_graph import run_materials_research_graph as _run

    return _run(*args, **kwargs)


def damask_copilot_workflow(*args, **kwargs):
    """Lazily import the v1 workflow runner."""
    from damask_copilot.graph.workflow import damask_copilot_workflow as _run

    return _run(*args, **kwargs)


def run_workflow(*args, **kwargs):
    """Lazily initialize and run the v1 workflow."""
    from damask_copilot.graph.workflow import run_workflow as _run

    return _run(*args, **kwargs)
