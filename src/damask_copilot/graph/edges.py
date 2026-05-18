"""Deterministic edge logic for the research graph."""

from __future__ import annotations

from damask_copilot.schemas.research_state import ResearchState


START = "__start__"
END = "__end__"


def next_node(current: str, state: ResearchState) -> str:
    """Return the next node key for the deterministic graph."""
    if current == START:
        return "research_manager"
    if current == "research_manager":
        return "parameter_database"
    if current == "parameter_database":
        return "material_knowledge"
    if current == "material_knowledge":
        return "simulation_planner"
    if current == "simulation_planner":
        return "input_builder"
    if current == "input_builder":
        return "checker"
    if current == "checker":
        if state.dry_run:
            return "report_writer"
        if state.checker_report and state.checker_report.ok:
            return "runner"
        return "report_writer"
    if current == "runner":
        return "postprocessor"
    if current == "postprocessor":
        return "scientific_critic"
    if current == "scientific_critic":
        return "report_writer"
    if current == "report_writer":
        return END
    return END
