"""Generic state and bridge helpers for the materials research graph."""

from __future__ import annotations

from typing import Any, TypedDict, cast

from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.critic_report import CriticReport
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.postprocess_report import PostprocessReport
from damask_copilot.schemas.project_plan import CandidateSimulation, ProjectPlan
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState, TraceEvent
from damask_copilot.schemas.run_report import RunReport
from damask_copilot.schemas.simulation_plan import SimulationPlan


class MaterialsResearchState(TypedDict, total=False):
    """Primary generic LangGraph state for materials research cases."""

    user_query: str
    mode: str
    use_llm: bool
    model: str | None
    max_iterations: int
    iteration: int
    user_files: list[str]
    literature_files: list[str]
    literature_sources: list[Any]
    experimental_files: list[str]
    user_constraints: dict[str, Any]
    research_case: dict[str, Any] | None
    research_questions: list[str]
    literature_review: dict[str, Any] | None
    experimental_data_summary: dict[str, Any] | None
    material_knowledge: dict[str, Any] | None
    hypotheses: list[dict[str, Any]]
    modeling_strategy: dict[str, Any] | None
    parameter_card: MaterialParameterCard | dict[str, Any] | None
    project_plan: ProjectPlan | dict[str, Any] | None
    project_milestones: list[str]
    current_milestone: str | None
    candidate_simulations: list[CandidateSimulation | dict[str, Any]]
    selected_simulation_id: str | None
    simulation_plan: SimulationPlan | dict[str, Any] | None
    workspace: str | None
    generated_files: GeneratedFiles | dict[str, Any] | None
    checker_report: CheckerReport | dict[str, Any] | None
    approval_status: str | None
    run_report: RunReport | dict[str, Any] | None
    postprocess_report: PostprocessReport | dict[str, Any] | None
    alignment_report: dict[str, Any] | None
    critic_report: CriticReport | dict[str, Any] | None
    iteration_decision: dict[str, Any] | None
    human_review_policy: dict[str, Any]
    pending_human_review: dict[str, Any] | None
    human_feedback_history: list[dict[str, Any]]
    final_report: str | None
    report_path: str | None
    trace: list[dict[str, Any]]
    errors: list[str]


def create_initial_materials_state(
    *,
    user_query: str,
    mode: str = "dry_run",
    use_llm: bool = False,
    model: str | None = None,
    max_iterations: int = 3,
    user_files: list[str] | None = None,
    literature_files: list[str] | None = None,
    literature_sources: list[Any] | None = None,
    experimental_files: list[str] | None = None,
    user_constraints: dict[str, Any] | None = None,
    human_review_policy: dict[str, Any] | None = None,
) -> MaterialsResearchState:
    """Create a fresh generic materials research state."""
    constraints = dict(user_constraints or {})
    policy = {
        "framing_review": constraints.get("framing_review", False),
        "before_run_review_type": "approval",
        "after_critique_review_type": "annotation",
        "after_critique_review": constraints.get("after_critique_review", False),
        "full_run_requires_approval": True,
        "review_low_confidence_parameters": True,
        "review_missing_metadata": True,
        "auto_approve_smoke_test": True,
    }
    if human_review_policy:
        policy.update(human_review_policy)
    return cast(MaterialsResearchState, {
        "user_query": user_query,
        "mode": mode,
        "use_llm": use_llm,
        "model": model,
        "max_iterations": max_iterations,
        "iteration": 0,
        "user_files": list(user_files or []),
        "literature_files": list(literature_files or []),
        "literature_sources": list(literature_sources or []),
        "experimental_files": list(experimental_files or []),
        "user_constraints": constraints,
        "research_case": None,
        "research_questions": [],
        "literature_review": None,
        "experimental_data_summary": None,
        "material_knowledge": None,
        "hypotheses": [],
        "modeling_strategy": None,
        "parameter_card": None,
        "project_plan": None,
        "project_milestones": [],
        "current_milestone": None,
        "candidate_simulations": [],
        "selected_simulation_id": None,
        "simulation_plan": None,
        "workspace": None,
        "generated_files": None,
        "checker_report": None,
        "approval_status": None,
        "run_report": None,
        "postprocess_report": None,
        "alignment_report": None,
        "critic_report": None,
        "iteration_decision": None,
        "human_review_policy": policy,
        "pending_human_review": None,
        "human_feedback_history": [],
        "final_report": None,
        "report_path": None,
        "trace": [],
        "errors": [],
    })


def append_error(state: MaterialsResearchState, message: str) -> MaterialsResearchState:
    """Append an error string to the generic graph state."""
    updated = dict(state)
    errors = list(updated.get("errors", []))
    errors.append(message)
    updated["errors"] = errors
    return cast(MaterialsResearchState, updated)


def append_trace(
    state: MaterialsResearchState,
    agent: str,
    event: str,
    details: dict[str, Any] | None = None,
) -> MaterialsResearchState:
    """Append a trace entry to the generic graph state."""
    updated = dict(state)
    trace = list(updated.get("trace", []))
    trace.append({"agent": agent, "event": event, "details": details or {}})
    updated["trace"] = trace
    return cast(MaterialsResearchState, updated)


def legacy_state_from_materials_state(state: MaterialsResearchState) -> ResearchState:
    """Bridge the generic graph state into the existing deterministic ResearchState."""
    research_case = dict(state.get("research_case") or {})
    parameter_card = _validate_optional(state.get("parameter_card"), MaterialParameterCard)
    project_plan = _validate_optional(state.get("project_plan"), ProjectPlan)
    candidate_simulations = [
        _validate_model(item, CandidateSimulation) for item in state.get("candidate_simulations", [])
    ]
    simulation_plan = _validate_optional(state.get("simulation_plan"), SimulationPlan)
    generated_files = _validate_optional(state.get("generated_files"), GeneratedFiles)
    checker_report = _validate_optional(state.get("checker_report"), CheckerReport)
    run_report = _validate_optional(state.get("run_report"), RunReport)
    postprocess_report = _validate_optional(state.get("postprocess_report"), PostprocessReport)
    critic_report = _validate_optional(state.get("critic_report"), CriticReport)
    material_system = research_case.get("material_system") or (
        parameter_card.material_id if parameter_card is not None else "generic_material"
    )
    objective = research_case.get("objective", "General materials research study")
    notes = _collect_notes(state)
    traces = [_validate_model(item, TraceEvent) for item in state.get("trace", [])]
    return ResearchState(
        user_query=state["user_query"],
        dry_run=state.get("mode") == "dry_run",
        use_llm=bool(state.get("use_llm", False)),
        smoke_test=state.get("mode") == "smoke_test",
        overwrite=bool(state.get("user_constraints", {}).get("allow_overwrite", False)),
        allow_full_run=bool(state.get("user_constraints", {}).get("approve", False)),
        model_name=state.get("model"),
        status="bridged",
        selected_material_key=parameter_card.material_id if parameter_card is not None else research_case.get("material_system"),
        goal=ResearchGoal(
            user_query=state["user_query"],
            material_system=material_system,
            objective=objective,
        ),
        material_card=parameter_card,
        project_plan=project_plan,
        project_milestones=list(state.get("project_milestones", [])),
        current_milestone=state.get("current_milestone"),
        candidate_simulations=candidate_simulations,
        selected_simulation_id=state.get("selected_simulation_id"),
        simulation_plan=simulation_plan,
        generated_files=generated_files,
        checker_report=checker_report,
        run_report=run_report,
        postprocess_report=postprocess_report,
        critic_report=critic_report,
        notes=notes,
        traces=traces,
        report_markdown=state.get("final_report"),
        report_path=state.get("report_path"),
    )


def materials_state_from_legacy(previous: MaterialsResearchState, legacy: ResearchState) -> MaterialsResearchState:
    """Merge legacy deterministic updates back into the generic materials state."""
    updated = dict(previous)
    if legacy.goal is not None:
        research_case = dict(updated.get("research_case") or {})
        research_case.setdefault("material_system", legacy.goal.material_system)
        research_case.setdefault("objective", legacy.goal.objective)
        research_case.setdefault("case_name", legacy.goal.user_query)
        updated["research_case"] = research_case
    if legacy.material_card is not None:
        updated["parameter_card"] = legacy.material_card
    if legacy.project_plan is not None:
        updated["project_plan"] = legacy.project_plan
    if legacy.project_milestones:
        updated["project_milestones"] = list(legacy.project_milestones)
    if legacy.current_milestone is not None:
        updated["current_milestone"] = legacy.current_milestone
    if legacy.candidate_simulations:
        updated["candidate_simulations"] = list(legacy.candidate_simulations)
    if legacy.selected_simulation_id is not None:
        updated["selected_simulation_id"] = legacy.selected_simulation_id
    if legacy.simulation_plan is not None:
        updated["simulation_plan"] = legacy.simulation_plan
        updated["workspace"] = legacy.simulation_plan.workspace
    if legacy.generated_files is not None:
        updated["generated_files"] = legacy.generated_files
        updated["workspace"] = legacy.generated_files.workspace_dir
    if legacy.checker_report is not None:
        updated["checker_report"] = legacy.checker_report
    if legacy.run_report is not None:
        updated["run_report"] = legacy.run_report
    if legacy.postprocess_report is not None:
        updated["postprocess_report"] = legacy.postprocess_report
    if legacy.critic_report is not None:
        updated["critic_report"] = legacy.critic_report
    if legacy.report_markdown is not None:
        updated["final_report"] = legacy.report_markdown
    if legacy.report_path is not None:
        updated["report_path"] = legacy.report_path
    updated["trace"] = [_model_to_dict(item) for item in legacy.traces]
    return cast(MaterialsResearchState, updated)


def _collect_notes(state: MaterialsResearchState) -> list[str]:
    notes: list[str] = []
    literature_review = dict(state.get("literature_review") or {})
    if literature_review.get("summary"):
        notes.append(str(literature_review["summary"]))
    for item in literature_review.get("uncertainties", []):
        if item not in notes:
            notes.append(str(item))
    material_knowledge = dict(state.get("material_knowledge") or {})
    if material_knowledge.get("summary") and material_knowledge["summary"] not in notes:
        notes.append(str(material_knowledge["summary"]))
    experimental_data = dict(state.get("experimental_data_summary") or {})
    if experimental_data.get("summary") and experimental_data["summary"] not in notes:
        notes.append(str(experimental_data["summary"]))
    project_plan = state.get("project_plan")
    if project_plan is not None:
        payload = _model_to_dict(project_plan)
        objective = payload.get("project_objective")
        if objective and objective not in notes:
            notes.append(str(objective))
        for item in payload.get("risks", []):
            if item not in notes:
                notes.append(str(item))
    return notes


def _validate_optional(payload: Any, model_cls):
    if payload is None:
        return None
    return _validate_model(payload, model_cls)


def _validate_model(payload: Any, model_cls):
    if isinstance(payload, model_cls):
        return payload
    validator = getattr(model_cls, "model_validate", None)
    if validator is not None:
        return validator(payload)
    return model_cls.parse_obj(payload)


def _model_to_dict(model: Any) -> dict[str, Any]:
    dumper = getattr(model, "model_dump", None)
    if dumper is not None:
        return dumper()
    if hasattr(model, "dict"):
        return model.dict()
    return dict(model)
