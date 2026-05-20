"""Routing helpers for the generic materials research graph."""

from __future__ import annotations

from damask_copilot.graph.materials_research_state import MaterialsResearchState


def route_after_checker(state: MaterialsResearchState) -> str:
    """Route after the deterministic simulation checker."""
    checker = state.get("checker_report")
    if checker is not None and getattr(checker, "status", None) == "blocked":
        return "research_report"
    return "human_review_before_run"


def route_after_human_review_before_run(state: MaterialsResearchState) -> str:
    """Route after the pre-run human review gate."""
    approval_status = state.get("approval_status")
    if state.get("mode") == "dry_run":
        return "scientific_critic"
    if approval_status in {"approved", "not_required"}:
        return "simulation_runner"
    return "research_report"


def route_after_runner(state: MaterialsResearchState) -> str:
    """Route after DAMASK execution."""
    run_report = state.get("run_report")
    if run_report is not None and getattr(run_report, "status", None) == "success":
        return "postprocessor"
    return "scientific_critic"


def route_after_iteration_decider(state: MaterialsResearchState) -> str:
    """Route according to the iteration decision action."""
    decision = dict(state.get("iteration_decision") or {})
    action = decision.get("action", "finish")
    mapping = {
        "revise_literature": "literature_agent",
        "revise_experimental_data": "experimental_data_agent",
        "revise_hypothesis": "hypothesis_agent",
        "revise_modeling_strategy": "modeling_strategy_agent",
        "revise_parameters": "parameter_agent",
        "revise_project_plan": "research_project_planner",
        "revise_simulation_plan": "simulation_planner",
        "request_human_input": "human_review_framing",
        "finish": "research_report",
    }
    return mapping.get(action, "research_report")
