"""Materials workflow compatibility wrappers around the unified v1 architecture."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from damask_copilot.graph.checkpoints import build_checkpointer
from damask_copilot.graph.materials_research_state import MaterialsResearchState
from damask_copilot.graph.state import ResearchState
from damask_copilot.graph.workflow import build_v1_graph, run_workflow
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
    """Build the materials research graph using the unified v1 workflow."""
    return build_v1_graph(
        checkpoint=checkpoint,
        use_llm=use_llm,
        model=model,
        llm_runner=llm_runner,
        agent_overrides=agent_overrides,
        checkpointer=checkpointer or build_checkpointer(checkpoint),
    )


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
    """Run the unified v1 materials workflow."""
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
    final_state = run_workflow(
        user_goal=payload["user_query"],
        workflow_type=None,
        max_iterations=payload["max_iterations"],
        mode=payload["mode"],
        use_llm=payload["use_llm"],
        model=payload["model"],
        state_overrides={
            "user_files": payload.get("user_files", []),
            "literature_files": payload.get("literature_files", []),
            "experimental_files": payload.get("experimental_files", []),
            "literature_sources": payload.get("literature_sources", []),
        },
    )
    if stream:
        for item in final_state.trace:
            print(f"[{item.get('agent')}] {_describe_trace_event(item, verbose=verbose)}")
    return _workflow_state_to_materials_state(final_state, thread_id)


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
    """Compatibility resume wrapper for the unified v1 workflow."""
    patch = dict(state_patch or {})
    user_goal = patch.get("user_goal") or patch.get("user_query") or comments or f"Resumed DAMASK workflow {thread_id}"
    final_state = run_workflow(
        user_goal=user_goal,
        workflow_type=None,
        max_iterations=int(patch.get("max_iterations", 1)),
        mode=patch.get("mode", "dry_run"),
        use_llm=bool(patch.get("use_llm", False)),
        model=patch.get("model"),
        state_overrides={
            key: value
            for key, value in patch.items()
            if key in {"user_files", "literature_files", "experimental_files", "literature_sources", "workspace"}
        },
    )
    final_state.append_trace(
        "materials_resume",
        "resume_compatibility_path",
        {"thread_id": thread_id, "decision": decision, "route_hint": route_hint},
    )
    if stream:
        for item in final_state.trace:
            print(f"[{item.get('agent')}] {_describe_trace_event(item, verbose=verbose)}")
    return _workflow_state_to_materials_state(final_state, thread_id)


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


def _describe_trace_event(event: dict[str, Any], *, verbose: bool = False) -> str:
    if verbose:
        return str(event)
    return event.get("event", "updated")


def _workflow_state_to_materials_state(state: ResearchState, thread_id: str | None) -> MaterialsResearchState:
    return {
        "user_query": state.user_goal,
        "mode": state.mode,
        "use_llm": state.use_llm,
        "model": state.model,
        "max_iterations": state.max_iterations,
        "iteration": state.iteration,
        "workspace": state.workspace,
        "final_report": state.final_report,
        "report_path": str(Path(state.workspace) / "research_report.md") if state.workspace else None,
        "trace": list(state.trace),
        "errors": list(state.errors),
        "__thread_id__": thread_id,
        "research_case": {
            "material_system": state.material_system,
            "workflow_type": state.workflow_type,
        },
    }
