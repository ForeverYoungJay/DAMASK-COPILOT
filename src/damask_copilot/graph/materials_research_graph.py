"""Generic experimental-data-guided materials research graph."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from langgraph.types import Command

from damask_copilot.graph.checkpoints import build_checkpointer
from damask_copilot.graph.materials_research_nodes import build_materials_research_nodes
from damask_copilot.graph.materials_research_routing import (
    route_after_checker,
    route_after_human_review_before_run,
    route_after_iteration_decider,
    route_after_runner,
)
from damask_copilot.graph.materials_research_state import (
    MaterialsResearchState,
    create_initial_materials_state,
)
from damask_copilot.llm.structured_runner import StructuredLLMRunner

DEFAULT_MATERIALS_CHECKPOINT_PATH = Path("workspaces/.damask_copilot/materials_graph_checkpoints.pkl")


def build_materials_research_graph(
    checkpoint: bool = True,
    *,
    use_llm: bool = False,
    model: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
    agent_overrides: dict[str, Any] | None = None,
    checkpointer: Any | None = None,
):
    """Build the generic LangGraph materials research graph."""
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(MaterialsResearchState)
    nodes = build_materials_research_nodes(
        use_llm=use_llm,
        model=model,
        llm_runner=llm_runner,
        agent_overrides=agent_overrides,
    )
    for name, node in nodes.items():
        graph.add_node(name, node)

    graph.add_edge(START, "research_manager")
    graph.add_edge("research_manager", "literature_agent")
    graph.add_edge("literature_agent", "experimental_data_agent")
    graph.add_edge("experimental_data_agent", "material_knowledge_agent")
    graph.add_edge("material_knowledge_agent", "hypothesis_agent")
    graph.add_edge("hypothesis_agent", "modeling_strategy_agent")
    graph.add_edge("modeling_strategy_agent", "parameter_agent")
    graph.add_edge("parameter_agent", "research_project_planner")
    graph.add_edge("research_project_planner", "human_review_framing")
    graph.add_edge("human_review_framing", "simulation_planner")
    graph.add_edge("simulation_planner", "damask_input_builder")
    graph.add_edge("damask_input_builder", "simulation_checker")
    graph.add_conditional_edges(
        "simulation_checker",
        route_after_checker,
        {
            "research_report": "research_report",
            "human_review_before_run": "human_review_before_run",
        },
    )
    graph.add_conditional_edges(
        "human_review_before_run",
        route_after_human_review_before_run,
        {
            "scientific_critic": "scientific_critic",
            "simulation_runner": "simulation_runner",
            "research_report": "research_report",
        },
    )
    graph.add_conditional_edges(
        "simulation_runner",
        route_after_runner,
        {
            "postprocessor": "postprocessor",
            "scientific_critic": "scientific_critic",
        },
    )
    graph.add_edge("postprocessor", "experiment_simulation_alignment")
    graph.add_edge("experiment_simulation_alignment", "scientific_critic")
    graph.add_edge("scientific_critic", "human_review_after_critique")
    graph.add_edge("human_review_after_critique", "iteration_decider")
    graph.add_conditional_edges(
        "iteration_decider",
        route_after_iteration_decider,
        {
            "literature_agent": "literature_agent",
            "experimental_data_agent": "experimental_data_agent",
            "hypothesis_agent": "hypothesis_agent",
            "modeling_strategy_agent": "modeling_strategy_agent",
            "parameter_agent": "parameter_agent",
            "research_project_planner": "research_project_planner",
            "simulation_planner": "simulation_planner",
            "human_review_framing": "human_review_framing",
            "research_report": "research_report",
        },
    )
    graph.add_edge("research_report", END)

    return graph.compile(checkpointer=checkpointer or build_checkpointer(checkpoint))


def run_materials_research_graph(
    user_query: str,
    *,
    mode: str = "dry_run",
    use_llm: bool = False,
    model: str | None = None,
    max_iterations: int = 3,
    user_files: list[str] | None = None,
    literature_files: list[str] | None = None,
    experimental_files: list[str] | None = None,
    literature_sources: list[Any] | None = None,
    source_list_files: list[str] | None = None,
    user_constraints: dict[str, Any] | None = None,
    checkpoint: bool = True,
    checkpoint_path: str | Path | None = None,
    thread_id: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
    agent_overrides: dict[str, Any] | None = None,
    stream: bool = True,
    verbose: bool = False,
) -> MaterialsResearchState:
    """Run the generic materials research graph."""
    import uuid

    payload = _resolve_materials_input(
        user_query=user_query,
        mode=mode,
        use_llm=use_llm,
        model=model,
        max_iterations=max_iterations,
        user_files=user_files,
        literature_files=literature_files,
        experimental_files=experimental_files,
        literature_sources=literature_sources,
        source_list_files=source_list_files,
        user_constraints=user_constraints,
    )
    initial_state = create_initial_materials_state(**payload)
    resolved_thread_id = thread_id or f"materials-research-{uuid.uuid4()}"
    checkpointer = build_checkpointer(checkpoint, storage_path=checkpoint_path or DEFAULT_MATERIALS_CHECKPOINT_PATH)
    app = build_materials_research_graph(
        checkpoint=checkpoint,
        use_llm=initial_state.get("use_llm", False),
        model=initial_state.get("model"),
        llm_runner=llm_runner,
        agent_overrides=agent_overrides,
        checkpointer=checkpointer,
    )
    config = {"configurable": {"thread_id": resolved_thread_id}}
    if stream:
        try:
            for update in app.stream(initial_state, config=config, stream_mode="updates"):
                for node_name, node_update in update.items():
                    print(f"[{node_name}] {_describe_node_update(node_name, node_update, verbose=verbose)}")
            snapshot = app.get_state(config)
            return _snapshot_to_state_dict(snapshot, resolved_thread_id)
        finally:
            _persist_checkpointer(checkpointer)
    try:
        result = app.invoke(initial_state, config=config)
        return _normalize_result_state(result, resolved_thread_id)
    finally:
        _persist_checkpointer(checkpointer)


def resume_materials_research_graph(
    *,
    thread_id: str,
    decision: str = "approve",
    comments: str | None = None,
    route_hint: str | None = None,
    state_patch: dict[str, Any] | None = None,
    checkpoint: bool = True,
    checkpoint_path: str | Path | None = None,
    llm_runner: StructuredLLMRunner | None = None,
    agent_overrides: dict[str, Any] | None = None,
    stream: bool = True,
    verbose: bool = False,
) -> MaterialsResearchState:
    """Resume a paused materials research graph from a persisted checkpoint."""
    checkpointer = build_checkpointer(checkpoint, storage_path=checkpoint_path or DEFAULT_MATERIALS_CHECKPOINT_PATH)
    app = build_materials_research_graph(
        checkpoint=checkpoint,
        use_llm=False,
        model=None,
        llm_runner=llm_runner,
        agent_overrides=agent_overrides,
        checkpointer=checkpointer,
    )
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = app.get_state(config)
    if not snapshot.next:
        raise ValueError(f"No paused materials research thread was found for thread_id='{thread_id}'.")

    payload: dict[str, Any] = {"decision": decision}
    if comments:
        payload["comments"] = comments
    if route_hint:
        payload["route_hint"] = route_hint
    if state_patch:
        payload["state_patch"] = state_patch

    command = Command(resume=payload)
    if stream:
        try:
            for update in app.stream(command, config=config, stream_mode="updates"):
                for node_name, node_update in update.items():
                    print(f"[{node_name}] {_describe_node_update(node_name, node_update, verbose=verbose)}")
            snapshot = app.get_state(config)
            return _snapshot_to_state_dict(snapshot, thread_id)
        finally:
            _persist_checkpointer(checkpointer)
    try:
        result = app.invoke(command, config=config)
        return _normalize_result_state(result, thread_id)
    finally:
        _persist_checkpointer(checkpointer)


def _resolve_materials_input(
    *,
    user_query: str,
    mode: str,
    use_llm: bool,
    model: str | None,
    max_iterations: int,
    user_files: list[str] | None = None,
    literature_files: list[str] | None = None,
    experimental_files: list[str] | None = None,
    literature_sources: list[Any] | None = None,
    source_list_files: list[str] | None = None,
    user_constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    input_path = Path(user_query)
    if input_path.exists() and input_path.suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(input_path.read_text(encoding="utf-8")) or {}
        user_files = list(payload.get("user_files", []))
        literature_files = list(payload.get("literature_files", []))
        experimental_files = list(payload.get("experimental_files", []))
        literature_sources = list(payload.get("literature_sources", []))
        source_list_files = list(payload.get("source_list_files", []))
        return {
            "user_query": payload.get("query", payload.get("user_query", "")),
            "mode": payload.get("mode", mode),
            "use_llm": bool(payload.get("use_llm", use_llm)),
            "model": payload.get("model", model),
            "max_iterations": int(payload.get("max_iterations", max_iterations)),
            "user_files": user_files or list(payload.get("user_files", [])),
            "literature_files": literature_files or list(payload.get("literature_files", [])),
            "experimental_files": experimental_files or list(payload.get("experimental_files", [])),
            "literature_sources": _expand_literature_sources(
                literature_sources or list(payload.get("literature_sources", [])),
                source_list_files or list(payload.get("source_list_files", [])),
            ),
            "user_constraints": dict(user_constraints or payload.get("user_constraints", {})),
        }
    return {
        "user_query": user_query,
        "mode": mode,
        "use_llm": use_llm,
        "model": model,
        "max_iterations": max_iterations,
        "user_files": list(user_files or []),
        "literature_files": list(literature_files or []),
        "experimental_files": list(experimental_files or []),
        "literature_sources": _expand_literature_sources(literature_sources, source_list_files),
        "user_constraints": dict(user_constraints or {}),
    }


def _expand_literature_sources(
    literature_sources: list[Any] | None,
    source_list_files: list[str] | None,
) -> list[Any]:
    expanded: list[Any] = list(literature_sources or [])
    for file_path in source_list_files or []:
        path = Path(file_path)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            entry = line.strip()
            if not entry or entry.startswith("#"):
                continue
            if entry not in expanded:
                expanded.append(entry)
    return expanded


def _describe_node_update(node_name: str, node_update: Any, *, verbose: bool = False) -> str:
    """Return a safe, human-readable summary for streamed node updates."""
    if verbose:
        if hasattr(node_update, "keys"):
            return f"updated: {sorted(node_update.keys())}"
        if isinstance(node_update, (list, tuple)):
            return f"updated: {type(node_update).__name__}(len={len(node_update)})"
        return f"updated: {type(node_update).__name__}"

    if node_name == "__interrupt__":
        return _describe_interrupt_update(node_update)

    if isinstance(node_update, dict):
        summary = _summarize_state_update(node_name, node_update)
        if summary:
            return summary
        return "updated"

    if isinstance(node_update, (list, tuple)):
        return f"updated ({type(node_update).__name__}, len={len(node_update)})"
    return f"updated ({type(node_update).__name__})"


def _summarize_state_update(node_name: str, state: dict[str, Any]) -> str:
    research_case = dict(state.get("research_case") or {})
    literature = dict(state.get("literature_review") or {})
    experimental = dict(state.get("experimental_data_summary") or {})
    strategy = dict(state.get("modeling_strategy") or {})
    checker = state.get("checker_report")
    run_report = state.get("run_report")
    postprocess = state.get("postprocess_report")
    alignment = dict(state.get("alignment_report") or {})
    critic = state.get("critic_report")
    parameter_card = state.get("parameter_card")
    project_plan = state.get("project_plan")
    plan = state.get("simulation_plan")

    if node_name == "research_manager":
        material = research_case.get("material_system", "unknown")
        loading = research_case.get("loading_mode", "unknown")
        return f"research case ready: material={material}, loading={loading}"
    if node_name == "literature_agent":
        providers = list(dict(literature.get("provider_summary") or {}).get("providers_succeeded", []))
        return (
            f"literature review ready: status={literature.get('status', 'unknown')}, "
            f"sources={len(literature.get('sources', []) or [])}, providers={providers or ['none']}"
        )
    if node_name == "experimental_data_agent":
        return f"experimental data: status={experimental.get('status', 'unknown')}"
    if node_name == "material_knowledge_agent":
        mechanism_count = len(dict(state.get("material_knowledge") or {}).get("mechanisms", []) or [])
        return f"material knowledge ready: mechanisms={mechanism_count}"
    if node_name == "hypothesis_agent":
        return f"hypotheses defined: count={len(state.get('hypotheses', []) or [])}"
    if node_name == "modeling_strategy_agent":
        return (
            f"strategy selected: abstraction={strategy.get('simulation_abstraction', 'unknown')}, "
            f"targets={strategy.get('comparison_targets', []) or ['none']}"
        )
    if node_name == "parameter_agent":
        flags = list(getattr(parameter_card, "parameters", {}).get("review_flags", [])) if parameter_card is not None else []
        material_id = getattr(parameter_card, "material_id", "unknown") if parameter_card is not None else "unknown"
        return f"parameter card ready: material={material_id}, review_flags={flags or ['none']}"
    if node_name == "research_project_planner":
        candidate_count = len(state.get("candidate_simulations", []) or [])
        next_action = getattr(project_plan, "next_action", None) if project_plan is not None else None
        if next_action is None and isinstance(project_plan, dict):
            next_action = project_plan.get("next_action")
        return f"project plan ready: candidates={candidate_count}, next_action={next_action or 'unknown'}"
    if node_name == "human_review_framing":
        return "waiting for human steering"
    if node_name == "simulation_planner" and plan is not None:
        return (
            f"plan ready: name={plan.name}, cells={plan.geometry.cells}, "
            f"grains={plan.geometry.grains}, strain={plan.loading.final_strain}, steps={plan.loading.steps}"
        )
    if node_name == "damask_input_builder":
        generated = state.get("generated_files")
        workspace_dir = getattr(generated, "workspace_dir", None)
        if workspace_dir is None and isinstance(generated, dict):
            workspace_dir = generated.get("workspace_dir")
        return f"inputs generated: workspace={workspace_dir or state.get('workspace', 'unknown')}"
    if node_name == "simulation_checker" and checker is not None:
        warnings = list(getattr(checker, "warnings", []))
        errors = list(getattr(checker, "errors", []))
        status = getattr(checker, "status", "unknown")
        return f"checker: status={status}, warnings={len(warnings)}, errors={len(errors)}"
    if node_name == "human_review_before_run":
        return "waiting for execution approval"
    if node_name == "simulation_runner" and run_report is not None:
        result_files = list(getattr(run_report, "result_files", []))
        return (
            f"run complete: status={getattr(run_report, 'status', 'unknown')}, "
            f"returncode={getattr(run_report, 'returncode', None)}, results={len(result_files)}"
        )
    if node_name == "postprocessor" and postprocess is not None:
        stress_csv = getattr(postprocess, "stress_strain_csv", None)
        return f"postprocess: status={getattr(postprocess, 'status', 'unknown')}, stress_strain_csv={'yes' if stress_csv else 'no'}"
    if node_name == "experiment_simulation_alignment":
        return f"alignment: status={alignment.get('status', 'unknown')}"
    if node_name == "scientific_critic" and critic is not None:
        next_steps = list(getattr(critic, "next_steps", []))
        return f"critique ready: next_steps={len(next_steps)}"
    if node_name == "human_review_after_critique":
        return "waiting for post-critique review"
    if node_name == "iteration_decider":
        decision = dict(state.get("iteration_decision") or {})
        return f"iteration decision: action={decision.get('action', 'finish')}"
    if node_name == "research_report":
        return f"report written: path={state.get('report_path', 'unknown')}"
    return ""


def _describe_interrupt_update(node_update: Any) -> str:
    stage = None
    review_type = None

    if isinstance(node_update, (list, tuple)) and node_update:
        first = node_update[0]
        value = getattr(first, "value", None)
        if isinstance(value, dict):
            stage = value.get("stage")
            review_type = value.get("review_type")
        elif isinstance(first, tuple) and len(first) >= 2 and isinstance(first[1], dict):
            stage = first[1].get("stage")
            review_type = first[1].get("review_type")

    parts = ["paused for human review"]
    if stage:
        parts.append(f"stage={stage}")
    if review_type:
        parts.append(f"type={review_type}")
    return ", ".join(parts)


def _normalize_result_state(result: Any, thread_id: str) -> MaterialsResearchState:
    state = dict(result)
    state["__thread_id__"] = thread_id
    return state


def _snapshot_to_state_dict(snapshot: Any, thread_id: str) -> MaterialsResearchState:
    state = dict(snapshot.values)
    if getattr(snapshot, "interrupts", ()):
        state["__interrupt__"] = list(snapshot.interrupts)
    state["__thread_id__"] = thread_id
    return state


def _persist_checkpointer(checkpointer: Any) -> None:
    if checkpointer is None:
        return
    persist = getattr(checkpointer, "persist", None)
    if persist is not None:
        persist()
