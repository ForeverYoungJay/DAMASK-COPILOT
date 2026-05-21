"""Runtime helper for the unified v1 DAMASK research workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from damask_copilot.graph.workflow import run_workflow
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.postprocess_report import PostprocessReport
from damask_copilot.schemas.run_report import RunReport


def run_research_graph(
    user_query: str,
    mode: str,
    use_llm: bool,
    model: str | None,
    max_iterations: int,
    *,
    approve: bool = False,
    allow_overwrite: bool = False,
    checkpoint: bool = True,
    thread_id: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
    agent_overrides: dict[str, Any] | None = None,
    stream: bool = True,
) -> dict[str, Any]:
    """Run the unified v1 workflow and return a compatibility dictionary."""
    query, resolved_mode, resolved_use_llm, resolved_model, resolved_max_iterations = _resolve_input(
        user_query=user_query,
        mode=mode,
        use_llm=use_llm,
        model=model,
        max_iterations=max_iterations,
    )
    final_state = run_workflow(
        user_goal=query,
        workflow_type=None,
        max_iterations=resolved_max_iterations,
        mode=resolved_mode,
        use_llm=resolved_use_llm,
        model=resolved_model,
        llm_runner=llm_runner,
        agent_overrides=agent_overrides,
    )
    if stream:
        for item in final_state.trace:
            print(f"[{item.get('agent')}] updated: {item.get('event')}")
    return _to_compat_state(final_state, approve=approve)


def _resolve_input(
    *,
    user_query: str,
    mode: str,
    use_llm: bool,
    model: str | None,
    max_iterations: int,
) -> tuple[str, str, bool, str | None, int]:
    input_path = Path(user_query)
    if input_path.exists() and input_path.suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(input_path.read_text(encoding="utf-8")) or {}
        return (
            payload.get("query", payload.get("user_query", "")),
            payload.get("mode", mode),
            bool(payload.get("use_llm", use_llm)),
            payload.get("model", model),
            int(payload.get("max_iterations", max_iterations)),
        )
    return user_query, mode, use_llm, model, max_iterations


def _describe_node_update(node_update: Any) -> str:
    """Return a safe, human-readable summary for streamed node updates."""
    if hasattr(node_update, "keys"):
        return str(sorted(node_update.keys()))
    if isinstance(node_update, (list, tuple)):
        return f"{type(node_update).__name__}(len={len(node_update)})"
    return type(node_update).__name__


def _to_compat_state(state, *, approve: bool) -> dict[str, Any]:
    validation = state.validation_result or {}
    run_result = state.run_result or {}
    postprocess = state.postprocessing_result or {}
    checker_report = state.checker_report or (
        CheckerReport(
            ok=validation.get("ok", False),
            status="passed" if validation.get("ok", False) else "blocked",
            errors=list(validation.get("errors", [])),
            warnings=list(validation.get("warnings", [])),
        )
        if validation
        else None
    )
    run_report = state.run_report or (
        RunReport(
            ok=run_result.get("ok", False),
            status=run_result.get("status", "skipped"),
            log_file=run_result.get("log_path"),
            result_files=list(run_result.get("result_files", [])),
            message=run_result.get("message") or run_result.get("error"),
        )
        if run_result
        else None
    )
    postprocess_report = state.postprocess_report or (
        PostprocessReport(
            ok=postprocess.get("ok", False),
            status=postprocess.get("status", "not_available"),
            result_file=(run_result.get("result_files") or [None])[0],
            summary=postprocess.get("error") or "v1 post-processing completed.",
            warnings=[],
        )
        if postprocess
        else None
    )
    report_path = state.report_path or (str(Path(state.workspace) / "research_report.md") if state.workspace else None)
    return {
        "user_query": state.user_goal,
        "mode": state.mode,
        "use_llm": state.use_llm,
        "model": state.model,
        "iteration": state.iteration,
        "max_iterations": state.max_iterations,
        "checker_report": checker_report,
        "run_report": run_report,
        "postprocess_report": postprocess_report,
        "approval_status": "approved" if state.mode in {"smoke_test", "full_run"} or approve else "not_required",
        "report_path": report_path,
        "final_report": state.final_report,
        "trace": list(state.trace),
        "next_action": state.next_action,
    }
