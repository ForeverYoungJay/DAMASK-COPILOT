"""Final v1 workflow for the 7-agent DAMASK Copilot architecture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from damask_copilot.agents.analysis_critic import AnalysisAndCriticAgent
from damask_copilot.agents.damask_execution import DAMASKExecutionAgent
from damask_copilot.agents.project_planner import ProjectPlannerAgent
from damask_copilot.agents.research_manager import ResearchManagerAgent
from damask_copilot.agents.research_report import ResearchReportAgent
from damask_copilot.agents.scientific_knowledge import ScientificKnowledgeAgent
from damask_copilot.agents.simulation_designer import SimulationDesignerAgent
from damask_copilot.graph.state import ResearchState, create_v1_state
from damask_copilot.graph.routing import route_after_analysis_action
from damask_copilot.memory.scientific_memory import ScientificMemoryLayer
from damask_copilot.tools.optimization import update_parameter_history
from damask_copilot.tools.postprocessing import postprocess_results
from damask_copilot.tools.validation import validate_damask_inputs


def damask_copilot_workflow(state: ResearchState) -> ResearchState:
    """Run the final v1 DAMASK Copilot workflow."""
    return _damask_copilot_workflow(state, agent_overrides=None)


def _damask_copilot_workflow(
    state: ResearchState,
    *,
    agent_overrides: dict[str, Any] | None = None,
    llm_runner=None,
) -> ResearchState:
    overrides = agent_overrides or {}
    workspace_root = str(_workspace_root_for_state(state))
    shared_memory = overrides.get("scientific_memory") or ScientificMemoryLayer(workspace_root=workspace_root)
    research_manager = overrides.get("research_manager") or ResearchManagerAgent(use_llm=state.use_llm, model_name=state.model, llm_runner=llm_runner)
    scientific_knowledge = overrides.get("scientific_knowledge") or ScientificKnowledgeAgent(
        use_llm=state.use_llm,
        model_name=state.model,
        llm_runner=llm_runner,
        scientific_memory=shared_memory,
        workspace_root=workspace_root,
    )
    project_planner = overrides.get("project_planner") or ProjectPlannerAgent(use_llm=state.use_llm, model_name=state.model, llm_runner=llm_runner)
    planner_override = overrides.get("simulation_planner")
    simulation_designer = overrides.get("simulation_designer") or SimulationDesignerAgent(
        workspace_root=workspace_root,
        scientific_memory=shared_memory,
    )
    checker_override = overrides.get("simulation_checker")
    execution_agent = overrides.get("damask_execution") or overrides.get("simulation_runner") or DAMASKExecutionAgent()
    postprocessor = overrides.get("damask_postprocessing") or overrides.get("postprocessor")
    analysis_agent = overrides.get("analysis_critic") or overrides.get("scientific_critic") or AnalysisAndCriticAgent(
        use_llm=state.use_llm,
        model_name=state.model,
        llm_runner=llm_runner,
        scientific_memory=shared_memory,
    )
    iteration_decider = overrides.get("iteration_decider")
    report_agent = overrides.get("research_report") or overrides.get("report_writer") or ResearchReportAgent(use_llm=state.use_llm, model_name=state.model, llm_runner=llm_runner)

    state = research_manager.run(state)
    _record_agent_execution(state, "research_manager")
    state = scientific_knowledge.run(state)
    _record_agent_execution(state, "scientific_knowledge")
    state = project_planner.run(state)
    _record_agent_execution(state, "project_planner")

    while state.iteration < state.max_iterations:
        if planner_override is not None:
            state = planner_override.run(state)
            _record_agent_execution(state, "simulation_planner_override")
        state = simulation_designer.run(state)
        _record_agent_execution(state, "simulation_designer")

        if checker_override is not None:
            state = checker_override.run(state)
            if state.validation_result is None and state.checker_report is not None:
                state.validation_result = {
                    "ok": state.checker_report.ok,
                    "errors": list(state.checker_report.errors),
                    "warnings": list(state.checker_report.warnings),
                }
            _record_agent_execution(state, "simulation_checker_override")
            if not (state.validation_result or {}).get("ok", False):
                state.next_action = {"type": "stop", "reason": "Legacy simulation_checker blocked execution."}
                break
        else:
            state.validation_result = validate_damask_inputs(state)
            _record_agent_execution(state, "damask_validation")
        if checker_override is None and not state.validation_result.get("ok", False):
            state = simulation_designer.repair_from_validation(state)
            _record_agent_execution(state, "repair_from_validation")
            state.validation_result = validate_damask_inputs(state)
            _record_agent_execution(state, "damask_validation")
            if not state.validation_result.get("ok", False):
                state.next_action = {"type": "request_human_review", "reason": "Validation failed after repair."}
                break

        state = execution_agent.run(state)
        _record_agent_execution(state, "damask_execution")
        if state.run_result is None and state.run_report is not None:
            state.run_result = {
                "ok": state.run_report.ok,
                "status": state.run_report.status,
                "log_path": state.run_report.log_file,
                "result_files": list(state.run_report.result_files),
                "message": state.run_report.message,
            }
        if (state.run_result or {}).get("status") in {"failed", "not_available"}:
            state = simulation_designer.repair_from_error(state)
            _record_agent_execution(state, "repair_from_error")
            state.run_result = state.run_result or {}
            state.iteration += 1
            continue

        if postprocessor is not None:
            state = postprocessor.run(state)
            if state.postprocessing_result is None and state.postprocess_report is not None:
                state.postprocessing_result = {
                    "ok": state.postprocess_report.ok,
                    "status": state.postprocess_report.status,
                    "summary": state.postprocess_report.summary,
                }
            _record_agent_execution(state, "damask_postprocessing_override")
        else:
            state.postprocessing_result = postprocess_results(state)
            _record_agent_execution(state, "damask_postprocessing")
        state = analysis_agent.run(state)
        _record_agent_execution(state, "analysis_critic")

        if iteration_decider is not None:
            decision_result = iteration_decider.run(state)
            if isinstance(decision_result, dict):
                state.trace = list(decision_result.get("trace", state.trace))
                state.iteration_decision = decision_result.get("iteration_decision")
            else:
                state = decision_result
            _record_agent_execution(state, "iteration_decider_override")
            continue_research = bool(getattr(state.iteration_decision, "continue_research", False)) if state.iteration_decision is not None else False
            state.next_action = {"type": "run_more_simulations", "reason": "Legacy iteration_decider requested another pass."} if continue_research else {"type": "stop", "reason": "Legacy iteration_decider stopped the workflow."}

        if (state.next_action or {}).get("type") == "stop":
            break

        history_update = update_parameter_history(state)
        state.parameter_history = history_update["parameter_history"]
        state.iteration += 1

    state = report_agent.run(state)
    _record_agent_execution(state, "research_report")
    return state


def run_workflow(
    user_goal: str,
    *,
    workflow_type: str | None = None,
    max_iterations: int = 3,
    mode: str = "dry_run",
    use_llm: bool = False,
    model: str | None = None,
    llm_runner=None,
    state_overrides: dict[str, Any] | None = None,
    agent_overrides: dict[str, Any] | None = None,
) -> ResearchState:
    """Convenience wrapper that initializes and runs the v1 workflow."""
    state = create_v1_state(
        user_goal=user_goal,
        workflow_type=workflow_type,
        max_iterations=max_iterations,
        mode=mode,
        use_llm=use_llm,
        model=model,
    )
    for key, value in (state_overrides or {}).items():
        setattr(state, key, value)
    return _damask_copilot_workflow(state, agent_overrides=agent_overrides, llm_runner=llm_runner)


def build_v1_graph(
    *,
    checkpoint: bool = False,
    use_llm: bool = False,
    model: str | None = None,
    llm_runner=None,
    agent_overrides: dict[str, Any] | None = None,
    checkpointer=None,
):
    """Build a LangGraph representation of the v1 workflow."""
    from langgraph.graph import END, START, StateGraph

    overrides = agent_overrides or {}
    shared_memory = overrides.get("scientific_memory") or ScientificMemoryLayer(workspace_root="workspaces")
    research_manager = overrides.get("research_manager") or ResearchManagerAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    scientific_knowledge = overrides.get("scientific_knowledge") or ScientificKnowledgeAgent(
        use_llm=use_llm,
        model_name=model,
        llm_runner=llm_runner,
        scientific_memory=shared_memory,
        workspace_root="workspaces",
    )
    project_planner = overrides.get("project_planner") or ProjectPlannerAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    simulation_designer = overrides.get("simulation_designer") or SimulationDesignerAgent(
        workspace_root="workspaces",
        scientific_memory=shared_memory,
    )
    execution_agent = overrides.get("damask_execution") or DAMASKExecutionAgent()
    analysis_agent = overrides.get("analysis_critic") or AnalysisAndCriticAgent(
        use_llm=use_llm,
        model_name=model,
        llm_runner=llm_runner,
        scientific_memory=shared_memory,
    )
    report_agent = overrides.get("research_report") or ResearchReportAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)

    graph = StateGraph(ResearchState)
    graph.add_node("research_manager", _stateful_node(research_manager.run))
    graph.add_node("scientific_knowledge", _stateful_node(scientific_knowledge.run))
    graph.add_node("project_planner", _stateful_node(project_planner.run))
    graph.add_node("simulation_designer", _stateful_node(simulation_designer.run))
    graph.add_node("damask_validation", _validate_node)
    graph.add_node("repair_from_validation", _stateful_node(simulation_designer.repair_from_validation))
    graph.add_node("damask_execution", _stateful_node(execution_agent.run))
    graph.add_node("repair_from_error", _stateful_node(simulation_designer.repair_from_error))
    graph.add_node("damask_postprocessing", _postprocess_node)
    graph.add_node("analysis_critic", _stateful_node(analysis_agent.run))
    graph.add_node("research_report", _stateful_node(report_agent.run))

    graph.add_edge(START, "research_manager")
    graph.add_edge("research_manager", "scientific_knowledge")
    graph.add_edge("scientific_knowledge", "project_planner")
    graph.add_edge("project_planner", "simulation_designer")
    graph.add_edge("simulation_designer", "damask_validation")
    graph.add_conditional_edges(
        "damask_validation",
        _route_after_validation,
        {
            "repair_from_validation": "repair_from_validation",
            "damask_execution": "damask_execution",
            "research_report": "research_report",
        },
    )
    graph.add_edge("repair_from_validation", "damask_validation")
    graph.add_conditional_edges(
        "damask_execution",
        _route_after_execution,
        {
            "repair_from_error": "repair_from_error",
            "damask_postprocessing": "damask_postprocessing",
        },
    )
    graph.add_edge("repair_from_error", "damask_validation")
    graph.add_edge("damask_postprocessing", "analysis_critic")
    graph.add_conditional_edges(
        "analysis_critic",
        route_after_analysis_action,
        {
            "simulation_designer": "simulation_designer",
            "research_report": "research_report",
        },
    )
    graph.add_edge("research_report", END)
    return graph.compile(checkpointer=checkpointer if checkpoint else None)


def _stateful_node(fn):
    def _node(payload: dict[str, Any] | ResearchState) -> ResearchState:
        state = _coerce_state(payload)
        return fn(state)

    return _node


def _validate_node(payload: dict[str, Any] | ResearchState) -> ResearchState:
    state = _coerce_state(payload)
    state.validation_result = validate_damask_inputs(state)
    return state


def _postprocess_node(payload: dict[str, Any] | ResearchState) -> ResearchState:
    state = _coerce_state(payload)
    state.postprocessing_result = postprocess_results(state)
    return state


def _coerce_state(payload: dict[str, Any] | ResearchState) -> ResearchState:
    if isinstance(payload, ResearchState):
        return payload
    return ResearchState.model_validate(payload)


def _workspace_root_for_state(state: ResearchState):
    if state.workspace:
        return Path(state.workspace).parent
    return Path("workspaces")


def _record_agent_execution(state: ResearchState, agent_name: str) -> None:
    trace_event = state.trace[-1] if state.trace else None
    record = {
        "sequence": len(state.agent_records) + 1,
        "agent": agent_name,
        "iteration": state.iteration,
        "mode": state.mode,
        "workflow_type": state.workflow_type,
        "material_system": state.material_system,
        "workspace": state.workspace,
        "trace_event": trace_event,
        "state_excerpt": _agent_state_excerpt(state, agent_name),
    }
    state.agent_records.append(record)
    _persist_agent_records(state)


def _persist_agent_records(state: ResearchState) -> None:
    if not state.workspace:
        return
    records_dir = Path(state.workspace) / "agent_records"
    records_dir.mkdir(parents=True, exist_ok=True)
    for record in state.agent_records:
        filename = f"{int(record['sequence']):02d}_{_slugify_record_name(str(record['agent']))}.json"
        (records_dir / filename).write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    index_payload = {
        "count": len(state.agent_records),
        "agents": [
            {
                "sequence": record["sequence"],
                "agent": record["agent"],
                "iteration": record["iteration"],
                "trace_event": (record.get("trace_event") or {}).get("event"),
            }
            for record in state.agent_records
        ],
    }
    (records_dir / "index.json").write_text(json.dumps(index_payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _agent_state_excerpt(state: ResearchState, agent_name: str) -> dict[str, Any]:
    mapping = {
        "research_manager": {
            "research_manager_output": state.research_manager_output,
            "workflow_type": state.workflow_type,
            "material_system": state.material_system,
            "needs": {
                "literature": state.needs_literature,
                "experimental_data": state.needs_experimental_data,
                "damask_simulation": state.needs_damask_simulation,
                "parameter_optimization": state.needs_parameter_optimization,
                "report": state.needs_report,
            },
        },
        "scientific_knowledge": {
            "literature_summary": state.literature_summary,
            "experimental_data": state.experimental_data,
            "known_parameters": state.known_parameters,
            "damask_capabilities": state.damask_capabilities,
        },
        "project_planner": {
            "project_plan": state.project_plan,
            "hypotheses": state.hypotheses,
        },
        "simulation_designer": {
            "simulation_spec": state.simulation_spec,
            "workspace": state.workspace,
            "generated_files": _jsonable(getattr(state, "generated_files", None)),
        },
        "simulation_planner_override": {
            "simulation_plan": _jsonable(state.simulation_plan),
            "simulation_spec": state.simulation_spec,
        },
        "simulation_checker_override": {
            "validation_result": state.validation_result,
            "checker_report": _jsonable(state.checker_report),
        },
        "damask_validation": {
            "validation_result": state.validation_result,
            "input_paths": {
                "material_yaml_path": state.material_yaml_path,
                "load_yaml_path": state.load_yaml_path,
                "geometry_path": state.geometry_path,
                "numerics_yaml_path": state.numerics_yaml_path,
            },
        },
        "repair_from_validation": {
            "validation_result": state.validation_result,
            "simulation_spec": state.simulation_spec,
        },
        "damask_execution": {
            "run_result": state.run_result,
            "run_report": _jsonable(state.run_report),
        },
        "repair_from_error": {
            "run_result": state.run_result,
            "simulation_spec": state.simulation_spec,
        },
        "damask_postprocessing": {
            "postprocessing_result": state.postprocessing_result,
            "postprocess_report": _jsonable(state.postprocess_report),
        },
        "damask_postprocessing_override": {
            "postprocessing_result": state.postprocessing_result,
            "postprocess_report": _jsonable(state.postprocess_report),
        },
        "analysis_critic": {
            "alignment_result": state.alignment_result,
            "critique": state.critique,
            "iteration_decision": _jsonable(state.iteration_decision),
            "next_action": state.next_action,
        },
        "iteration_decider_override": {
            "iteration_decision": _jsonable(state.iteration_decision),
            "next_action": state.next_action,
        },
        "research_report": {
            "report_path": state.report_path,
            "final_report_preview": (state.final_report or "")[:1000],
            "next_action": state.next_action,
        },
    }
    return mapping.get(agent_name, {"state": state.model_dump(mode="json")})


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    dumper = getattr(value, "model_dump", None)
    if dumper is not None:
        return dumper()
    if hasattr(value, "dict"):
        return value.dict()
    return value


def _slugify_record_name(value: str) -> str:
    text = value.lower().replace(" ", "_")
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in text).strip("_")


def _route_after_validation(payload: dict[str, Any]) -> str:
    state = _coerce_state(payload)
    result = state.validation_result or {}
    if result.get("ok", False):
        return "damask_execution"
    repair_count = _count_trace_events(state, "simulation_designer", "repaired_from_validation")
    return "repair_from_validation" if repair_count < 1 else "research_report"


def _route_after_execution(payload: dict[str, Any]) -> str:
    state = _coerce_state(payload)
    status = (state.run_result or {}).get("status")
    if status in {"failed", "not_available"}:
        return "repair_from_error"
    return "damask_postprocessing"


def _count_trace_events(state: ResearchState, agent: str, event: str) -> int:
    return sum(
        1
        for item in state.trace
        if item.get("agent") == agent and item.get("event") == event
    )
