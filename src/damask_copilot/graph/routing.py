"""Conditional routing logic for the LangGraph research graph."""

from __future__ import annotations

from damask_copilot.graph.state import DamaskResearchState


def route_after_checker(state: DamaskResearchState) -> str:
    checker = state.get("checker_report")
    if checker is not None and getattr(checker, "status", None) == "blocked":
        return "report_writer"
    return "approval_gate"


def route_after_approval(state: DamaskResearchState) -> str:
    approval_status = state.get("approval_status")
    if state.get("mode") == "dry_run":
        return "scientific_critic"
    if approval_status in {"approved", "not_required"}:
        return "simulation_runner"
    return "report_writer"


def route_after_runner(state: DamaskResearchState) -> str:
    run_report = state.get("run_report")
    if run_report is not None and getattr(run_report, "status", None) == "success":
        return "postprocessor"
    return "scientific_critic"


def route_after_iteration_decider(state: DamaskResearchState) -> str:
    decision = state.get("iteration_decision")
    should_continue = bool(getattr(decision, "continue_research", False)) if decision is not None else False
    if should_continue and state.get("iteration", 0) < state.get("max_iterations", 1):
        return "simulation_planner"
    return "report_writer"
