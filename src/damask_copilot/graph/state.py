"""Typed state models and legacy bridge helpers for DAMASK Copilot graphs."""

from __future__ import annotations

from typing import Any, TypedDict, cast

from pydantic import BaseModel, Field

from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.critic_report import CriticReport
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.llm_outputs import (
    IterationDecisionOutput,
    LiteratureAgentOutput,
    MaterialKnowledgeOutput,
    ReportWriterOutput,
    ResearchManagerOutput,
    ScientificCriticOutput,
    SimulationPlannerOutput,
)
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.postprocess_report import PostprocessReport
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState as LegacyResearchState, TraceEvent
from damask_copilot.schemas.run_report import RunReport
from damask_copilot.schemas.simulation_plan import SimulationPlan


class ResearchState(BaseModel):
    """Shared v1 state for the 7-agent DAMASK Copilot workflow."""

    user_goal: str = Field(..., min_length=1)
    workflow_type: str | None = None
    material_system: str | None = None
    objective: str | None = None
    reasoning_summary: str | None = None
    research_manager_output: dict[str, Any] | None = None
    needs_literature: bool = False
    needs_experimental_data: bool = False
    needs_damask_simulation: bool = True
    needs_parameter_optimization: bool = False
    needs_report: bool = True
    experimental_data: dict[str, Any] | None = None

    literature_summary: dict[str, Any] | None = None
    known_parameters: dict[str, Any] | None = None
    damask_capabilities: dict[str, Any] | None = None

    project_plan: dict[str, Any] | None = None
    hypotheses: list[dict[str, Any]] = Field(default_factory=list)

    simulation_plan: Any | None = None
    simulation_spec: dict[str, Any] | None = None
    material_yaml_path: str | None = None
    load_yaml_path: str | None = None
    geometry_path: str | None = None
    numerics_yaml_path: str | None = None
    workspace: str | None = None
    generated_files: GeneratedFiles | None = None

    validation_result: dict[str, Any] | None = None
    run_result: dict[str, Any] | None = None
    postprocessing_result: dict[str, Any] | None = None
    alignment_result: dict[str, Any] | None = None
    checker_report: CheckerReport | None = None
    run_report: RunReport | None = None
    postprocess_report: PostprocessReport | None = None
    critic_report: CriticReport | None = None

    critique: dict[str, Any] | None = None
    next_action: dict[str, Any] | None = None
    iteration_decision: IterationDecisionOutput | dict[str, Any] | None = None

    iteration: int = 0
    max_iterations: int = 3

    final_report: str | None = None
    report_path: str | None = None

    project_name: str | None = None
    project_dir: str | None = None
    user_files: list[str] = Field(default_factory=list)
    literature_files: list[str] = Field(default_factory=list)
    literature_sources: list[Any] = Field(default_factory=list)
    source_list_files: list[str] = Field(default_factory=list)
    experimental_files: list[str] = Field(default_factory=list)
    parameter_history: list[dict[str, Any]] = Field(default_factory=list)
    agent_records: list[dict[str, Any]] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    use_llm: bool = False
    model: str | None = None
    mode: str = "dry_run"

    def append_trace(self, agent: str, event: str, details: dict[str, Any] | None = None) -> "ResearchState":
        """Append a trace entry to the mutable v1 state."""
        self.trace.append({"agent": agent, "event": event, "details": details or {}})
        return self

    def append_error(self, message: str) -> "ResearchState":
        """Append an error entry to the mutable v1 state."""
        self.errors.append(message)
        return self

    @property
    def traces(self) -> list[dict[str, Any]]:
        """Compatibility alias for legacy state.traces access."""
        return self.trace

    @property
    def selected_material_key(self) -> str | None:
        """Compatibility alias for legacy selected_material_key access."""
        return self.material_system

    @selected_material_key.setter
    def selected_material_key(self, value: str | None) -> None:
        """Compatibility alias for legacy selected_material_key mutation."""
        self.material_system = value


def create_v1_state(
    *,
    user_goal: str,
    workflow_type: str | None = None,
    max_iterations: int = 3,
    mode: str = "dry_run",
    use_llm: bool = False,
    model: str | None = None,
) -> ResearchState:
    """Create a fresh v1 workflow state."""
    return ResearchState(
        user_goal=user_goal,
        workflow_type=workflow_type,
        max_iterations=max_iterations,
        mode=mode,
        use_llm=use_llm,
        model=model,
    )


class DamaskResearchState(TypedDict, total=False):
    """Primary LangGraph state for DAMASK Copilot."""

    user_query: str
    mode: str
    use_llm: bool
    model: str | None
    selected_material_key: str | None
    research_goal: ResearchGoal | dict[str, Any] | None
    research_manager_output: ResearchManagerOutput | dict[str, Any] | None
    literature_notes: list[str]
    material_knowledge: MaterialKnowledgeOutput | dict[str, Any] | None
    material_card: MaterialParameterCard | dict[str, Any] | None
    simulation_plan: SimulationPlan | dict[str, Any] | None
    simulation_planner_output: SimulationPlannerOutput | dict[str, Any] | None
    workspace: str | None
    generated_files: GeneratedFiles | dict[str, Any] | None
    checker_report: CheckerReport | dict[str, Any] | None
    approval_request: dict[str, Any] | None
    approval_status: str | None
    run_report: RunReport | dict[str, Any] | None
    postprocess_report: PostprocessReport | dict[str, Any] | None
    critic_report: CriticReport | dict[str, Any] | None
    scientific_critic_output: ScientificCriticOutput | dict[str, Any] | None
    report_writer_output: ReportWriterOutput | dict[str, Any] | None
    iteration_decision: IterationDecisionOutput | dict[str, Any] | None
    iteration: int
    max_iterations: int
    final_report: str | None
    report_path: str | None
    trace: list[dict[str, Any]]
    errors: list[str]


def create_initial_state(
    *,
    user_query: str,
    mode: str,
    use_llm: bool,
    model: str | None,
    max_iterations: int,
    explicit_approval: bool = False,
    allow_overwrite: bool = False,
) -> DamaskResearchState:
    """Create a fresh LangGraph research state."""
    return cast(DamaskResearchState, {
        "user_query": user_query,
        "mode": mode,
        "use_llm": use_llm,
        "model": model,
        "selected_material_key": None,
        "research_goal": None,
        "research_manager_output": None,
        "literature_notes": [],
        "material_knowledge": None,
        "material_card": None,
        "simulation_plan": None,
        "simulation_planner_output": None,
        "workspace": None,
        "generated_files": None,
        "checker_report": None,
        "approval_request": {"explicit_approval": explicit_approval, "allow_overwrite": allow_overwrite},
        "approval_status": None,
        "run_report": None,
        "postprocess_report": None,
        "critic_report": None,
        "scientific_critic_output": None,
        "report_writer_output": None,
        "iteration_decision": None,
        "iteration": 0,
        "max_iterations": max_iterations,
        "final_report": None,
        "report_path": None,
        "trace": [],
        "errors": [],
    })


def legacy_state_from_graph(state: DamaskResearchState) -> LegacyResearchState:
    """Translate LangGraph state into the existing Pydantic ResearchState."""
    literature_notes = list(state.get("literature_notes", []))
    material_knowledge = _validate_optional(state.get("material_knowledge"), MaterialKnowledgeOutput)
    if material_knowledge is not None:
        literature_notes.extend(material_knowledge.planning_considerations)
        if material_knowledge.knowledge_summary not in literature_notes:
            literature_notes.append(material_knowledge.knowledge_summary)

    traces = [_validate_model(item, TraceEvent) for item in state.get("trace", [])]

    return LegacyResearchState(
        user_query=state["user_query"],
        dry_run=state.get("mode") == "dry_run",
        use_llm=bool(state.get("use_llm", False)),
        smoke_test=state.get("mode") == "smoke_test",
        overwrite=bool(state.get("approval_request", {}).get("allow_overwrite", False)),
        allow_full_run=bool(state.get("approval_request", {}).get("explicit_approval", False)),
        model_name=state.get("model"),
        goal=_validate_optional(state.get("research_goal"), ResearchGoal),
        research_manager_output=_validate_optional(state.get("research_manager_output"), ResearchManagerOutput),
        selected_material_key=state.get("selected_material_key"),
        material_card=_validate_optional(state.get("material_card"), MaterialParameterCard),
        material_knowledge_output=material_knowledge,
        simulation_plan=_validate_optional(state.get("simulation_plan"), SimulationPlan),
        simulation_planner_output=_validate_optional(state.get("simulation_planner_output"), SimulationPlannerOutput),
        generated_files=_validate_optional(state.get("generated_files"), GeneratedFiles),
        checker_report=_validate_optional(state.get("checker_report"), CheckerReport),
        run_report=_validate_optional(state.get("run_report"), RunReport),
        postprocess_report=_validate_optional(state.get("postprocess_report"), PostprocessReport),
        critic_report=_validate_optional(state.get("critic_report"), CriticReport),
        scientific_critic_output=_validate_optional(state.get("scientific_critic_output"), ScientificCriticOutput),
        notes=literature_notes,
        traces=traces,
        report_markdown=state.get("final_report"),
        report_path=state.get("report_path"),
    )


def graph_state_from_legacy(previous: DamaskResearchState, legacy: LegacyResearchState) -> DamaskResearchState:
    """Merge updates from the existing Pydantic state back into the LangGraph state."""
    next_state = dict(previous)
    next_state["selected_material_key"] = legacy.selected_material_key
    next_state["research_goal"] = legacy.goal
    next_state["research_manager_output"] = legacy.research_manager_output
    next_state["material_card"] = legacy.material_card
    next_state["material_knowledge"] = legacy.material_knowledge_output or next_state.get("material_knowledge")
    next_state["simulation_plan"] = legacy.simulation_plan
    next_state["simulation_planner_output"] = legacy.simulation_planner_output
    next_state["workspace"] = legacy.simulation_plan.name if legacy.simulation_plan else next_state.get("workspace")
    next_state["generated_files"] = legacy.generated_files
    next_state["checker_report"] = legacy.checker_report
    next_state["run_report"] = legacy.run_report
    next_state["postprocess_report"] = legacy.postprocess_report
    next_state["critic_report"] = legacy.critic_report
    next_state["scientific_critic_output"] = legacy.scientific_critic_output
    next_state["report_path"] = legacy.report_path
    next_state["final_report"] = legacy.report_markdown
    next_state["trace"] = [_model_to_dict(item) for item in legacy.traces]
    next_state.setdefault("literature_notes", [])
    return cast(DamaskResearchState, next_state)


def append_error(state: DamaskResearchState, message: str) -> DamaskResearchState:
    """Append an error string to state.errors."""
    updated = dict(state)
    errors = list(updated.get("errors", []))
    errors.append(message)
    updated["errors"] = errors
    return cast(DamaskResearchState, updated)


def append_trace(state: DamaskResearchState, agent: str, event: str, details: dict[str, Any] | None = None) -> DamaskResearchState:
    """Append a trace entry to the LangGraph state."""
    updated = dict(state)
    trace = list(updated.get("trace", []))
    trace.append({"agent": agent, "event": event, "details": details or {}})
    updated["trace"] = trace
    return cast(DamaskResearchState, updated)


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
