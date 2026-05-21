"""Node factories for the generic materials research graph.

This module still exposes the legacy/hybrid node builder for compatibility, but
the preferred v1 architecture is the 7-agent workflow in
`damask_copilot.graph.workflow`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from damask_copilot.agents.analysis_critic import AnalysisAndCriticAgent
from damask_copilot.agents.damask_execution import DAMASKExecutionAgent
from damask_copilot.agents.damask_input_builder import DAMASKInputBuilderAgent
from damask_copilot.agents.experiment_simulation_alignment import ExperimentSimulationAlignmentAgent
from damask_copilot.agents.experimental_data_agent import ExperimentalDataAgent
from damask_copilot.agents.human_review_agent import HumanReviewAgent
from damask_copilot.agents.hypothesis_agent import HypothesisAgent
from damask_copilot.agents.iteration_decision import IterationDecisionAgent
from damask_copilot.agents.literature_agent import LiteratureAgent
from damask_copilot.agents.material_knowledge import MaterialKnowledgeAgent
from damask_copilot.agents.modeling_strategy_agent import ModelingStrategyAgent
from damask_copilot.agents.parameter_agent import ParameterAgent
from damask_copilot.agents.postprocessor import PostProcessingAgent
from damask_copilot.agents.project_planner import ProjectPlannerAgent
from damask_copilot.agents.research_manager import ResearchManagerAgent
from damask_copilot.agents.research_project_planner import ResearchProjectPlannerAgent
from damask_copilot.agents.research_report import ResearchReportAgent
from damask_copilot.agents.scientific_knowledge import ScientificKnowledgeAgent
from damask_copilot.agents.scientific_critic import ScientificCriticAgent
from damask_copilot.agents.simulation_checker import SimulationCheckerAgent
from damask_copilot.agents.simulation_designer import SimulationDesignerAgent
from damask_copilot.agents.simulation_planner import SimulationPlannerAgent
from damask_copilot.agents.simulation_runner import SimulationRunnerAgent
from damask_copilot.graph.materials_research_state import (
    MaterialsResearchState,
    append_error,
    append_trace,
    legacy_state_from_materials_state,
    materials_state_from_legacy,
)
from damask_copilot.llm.structured_runner import StructuredLLMRunner


def build_v1_materials_research_nodes(
    *,
    use_llm: bool = False,
    model: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
) -> dict[str, Any]:
    """Build the preferred 7-agent v1 node mapping."""
    return {
        "research_manager": ResearchManagerAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
        "scientific_knowledge": ScientificKnowledgeAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
        "project_planner": ProjectPlannerAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
        "simulation_designer": SimulationDesignerAgent(),
        "damask_execution": DAMASKExecutionAgent(),
        "analysis_critic": AnalysisAndCriticAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
        "research_report": ResearchReportAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner),
    }


def build_materials_research_nodes(
    *,
    use_llm: bool = False,
    model: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
    agent_overrides: dict[str, Any] | None = None,
) -> dict[str, Callable[[MaterialsResearchState], MaterialsResearchState]]:
    """Build node callables for the generic materials research graph."""
    overrides = agent_overrides or {}
    research_manager = overrides.get("research_manager") or ResearchManagerAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    literature_agent = overrides.get("literature_agent") or LiteratureAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    experimental_data_agent = overrides.get("experimental_data_agent") or ExperimentalDataAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    material_knowledge = overrides.get("material_knowledge_agent") or MaterialKnowledgeAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    hypothesis_agent = overrides.get("hypothesis_agent") or HypothesisAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    modeling_strategy_agent = overrides.get("modeling_strategy_agent") or ModelingStrategyAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    parameter_agent = overrides.get("parameter_agent") or ParameterAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    research_project_planner = overrides.get("research_project_planner") or ResearchProjectPlannerAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    simulation_planner = overrides.get("simulation_planner") or SimulationPlannerAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    experiment_simulation_alignment = overrides.get("experiment_simulation_alignment") or ExperimentSimulationAlignmentAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    scientific_critic = overrides.get("scientific_critic") or ScientificCriticAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    iteration_decider = overrides.get("iteration_decider") or IterationDecisionAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)
    research_report = overrides.get("research_report") or ResearchReportAgent(use_llm=use_llm, model_name=model, llm_runner=llm_runner)

    return {
        "research_manager": _node("research_manager", _run_research_manager(research_manager)),
        "literature_agent": _node("literature_agent", _run_literature_agent(literature_agent)),
        "experimental_data_agent": _node("experimental_data_agent", experimental_data_agent),
        "material_knowledge_agent": _node("material_knowledge_agent", _run_material_knowledge_agent(material_knowledge)),
        "hypothesis_agent": _node("hypothesis_agent", hypothesis_agent),
        "modeling_strategy_agent": _node("modeling_strategy_agent", modeling_strategy_agent),
        "parameter_agent": _node("parameter_agent", parameter_agent),
        "research_project_planner": _node("research_project_planner", research_project_planner),
        "human_review_framing": _node("human_review_framing", HumanReviewAgent("human_review_framing")),
        "simulation_planner": _node("simulation_planner", _run_simulation_planner(simulation_planner)),
        "damask_input_builder": _legacy_node("damask_input_builder", overrides.get("damask_input_builder") or DAMASKInputBuilderAgent()),
        "simulation_checker": _legacy_node("simulation_checker", overrides.get("simulation_checker") or SimulationCheckerAgent()),
        "human_review_before_run": _node("human_review_before_run", HumanReviewAgent("human_review_before_run")),
        "simulation_runner": _legacy_node("simulation_runner", overrides.get("simulation_runner") or SimulationRunnerAgent()),
        "postprocessor": _legacy_node("postprocessor", overrides.get("postprocessor") or PostProcessingAgent()),
        "experiment_simulation_alignment": _node("experiment_simulation_alignment", experiment_simulation_alignment),
        "scientific_critic": _node("scientific_critic", _run_scientific_critic(scientific_critic)),
        "human_review_after_critique": _node("human_review_after_critique", HumanReviewAgent("human_review_after_critique")),
        "iteration_decider": _node("iteration_decider", iteration_decider),
        "research_report": _node("research_report", research_report),
    }


def _node(name: str, agent) -> Callable[[MaterialsResearchState], MaterialsResearchState]:
    def _wrapped(state: MaterialsResearchState) -> MaterialsResearchState:
        try:
            return agent.run(state)
        except Exception as exc:
            if _is_graph_interrupt(exc):
                raise
            errored = append_error(state, f"{name}: {type(exc).__name__}: {exc}")
            return append_trace(errored, name, "error", {"error": f"{type(exc).__name__}: {exc}"})

    return _wrapped


def _legacy_node(name: str, agent) -> Callable[[MaterialsResearchState], MaterialsResearchState]:
    def _wrapped(state: MaterialsResearchState) -> MaterialsResearchState:
        try:
            legacy_state = legacy_state_from_materials_state(state)
            updated_legacy = agent.run(legacy_state)
            return materials_state_from_legacy(state, updated_legacy)
        except Exception as exc:
            if _is_graph_interrupt(exc):
                raise
            errored = append_error(state, f"{name}: {type(exc).__name__}: {exc}")
            return append_trace(errored, name, "error", {"error": f"{type(exc).__name__}: {exc}"})

    return _wrapped


def _run_research_manager(agent: ResearchManagerAgent):
    class _ResearchManagerWrapper:
        def run(self, state: MaterialsResearchState) -> MaterialsResearchState:
            legacy_state = legacy_state_from_materials_state(state)
            updated_legacy = agent.run(legacy_state)
            updated = materials_state_from_legacy(state, updated_legacy)
            goal = updated_legacy.goal
            research_case = {
                "material_system": goal.material_system if goal else "generic_material",
                "objective": goal.objective if goal else "General materials research study",
                "loading_mode": _infer_loading_mode(state["user_query"], goal.objective if goal else ""),
                "microstructure": _infer_microstructure(state["user_query"]),
                "structure": _infer_structure(state["user_query"], goal.material_system if goal else ""),
                "has_experimental_data": bool(state.get("experimental_files") or state.get("user_files")),
                "has_literature": bool(state.get("literature_sources") or state.get("literature_files")),
                "requires_complex_loading": _requires_complex_loading(state["user_query"]),
            }
            updated["research_case"] = research_case
            updated["research_questions"] = _build_research_questions(state["user_query"], research_case)
            updated["workspace"] = str(Path("workspaces") / _slugify(f"{research_case['material_system']}_{research_case['loading_mode']}"))
            return append_trace(updated, "research_manager", "research_case_defined", research_case)

    return _ResearchManagerWrapper()


def _run_literature_agent(agent: LiteratureAgent):
    class _LiteratureWrapper:
        def run(self, state: MaterialsResearchState) -> MaterialsResearchState:
            pseudo_state = {
                "user_query": state["user_query"],
                "research_goal": state.get("research_case"),
                "mode": state.get("mode"),
                "use_llm": state.get("use_llm", False),
                "model": state.get("model"),
                "workspace": state.get("workspace"),
                "literature_files": list(state.get("literature_files", [])),
                "literature_sources": list(state.get("literature_sources", [])),
                "literature_notes": [],
                "trace": [],
                "errors": [],
            }
            updated_pseudo = agent.run(pseudo_state)
            external = dict(updated_pseudo.get("literature_external_results", {}))
            analysis = dict(updated_pseudo.get("literature_analysis", {}))
            provided_sources = list(state.get("literature_sources", []))
            local_files = list(external.get("local_files", [])) or list(state.get("literature_files", []))
            status = "literature_review_ready" if (provided_sources or local_files or external.get("used_external_retrieval") or external.get("used_local_files")) else "literature_missing"
            normalized_sources = _normalize_literature_sources(
                provided_sources=provided_sources,
                resolved_sources=list(external.get("resolved_sources", [])),
                user_query=state["user_query"],
            )
            summary = (
                analysis.get("summary")
                or external.get("summary")
                or " ".join(updated_pseudo.get("literature_notes", []))
                or "No literature review content was generated."
            )
            notes = list(updated_pseudo.get("literature_notes", []))
            review = {
                "status": status,
                "sources": normalized_sources,
                "summary": summary,
                "retrieval_stages": list(external.get("retrieval_stages", [])),
                "notes": notes,
                "mechanisms": analysis.get("relevant_mechanisms") or _extract_mechanisms(" ".join(notes) or summary),
                "candidate_constitutive_models": analysis.get("candidate_constitutive_models") or _extract_model_hints(" ".join(notes) or summary),
                "reported_parameters": [],
                "experimental_conditions": analysis.get("experimental_conditions") or _extract_experimental_conditions(notes),
                "observables_for_validation": analysis.get("observables_for_validation") or _extract_validation_observables(notes),
                "planning_implications": list(analysis.get("planning_implications", [])),
                "unsupported_claims": list(analysis.get("unsupported_claims", [])),
                "evidence_gaps": list(analysis.get("evidence_gaps", [])),
                "local_files": local_files,
                "uncertainties": list(external.get("uncertainties", []))
                or (["Unsupported claims should be verified by the user."] if not provided_sources else []),
                "provider_summary": {
                    "providers_attempted": external.get("providers_attempted", []),
                    "providers_succeeded": external.get("providers_succeeded", []),
                },
            }
            updated = dict(state)
            updated["literature_review"] = review
            return append_trace(updated, "literature_agent", "literature_review_compiled", {"status": status, "source_count": len(provided_sources)})

    return _LiteratureWrapper()


def _run_material_knowledge_agent(agent: MaterialKnowledgeAgent):
    class _MaterialKnowledgeWrapper:
        def run(self, state: MaterialsResearchState) -> MaterialsResearchState:
            legacy_state = legacy_state_from_materials_state(state)
            updated_legacy = agent.run(legacy_state)
            updated = materials_state_from_legacy(state, updated_legacy)
            mk = updated_legacy.material_knowledge_output
            literature = dict(state.get("literature_review") or {})
            experimental = dict(state.get("experimental_data_summary") or {})
            summary_parts = []
            if getattr(mk, "knowledge_summary", None):
                summary_parts.append(getattr(mk, "knowledge_summary"))
            if literature.get("summary"):
                summary_parts.append(f"Literature context: {literature['summary']}")
            if experimental.get("interpretation_summary") and experimental.get("status") != "experimental_data_missing":
                summary_parts.append(f"Experimental context: {experimental['interpretation_summary']}")
            mechanisms = list(literature.get("mechanisms", []))
            for item in literature.get("planning_implications", [])[:2]:
                if item not in mechanisms:
                    mechanisms.append(item)
            unknowns = list(literature.get("uncertainties", []))
            for item in literature.get("evidence_gaps", []):
                if item not in unknowns:
                    unknowns.append(item)
            if experimental.get("needs_human_correction"):
                for item in experimental.get("metadata_questions", []) or ["Experimental metadata missing."]:
                    if item not in unknowns:
                        unknowns.append(item)
            updated["material_knowledge"] = {
                "summary": " ".join(summary_parts) if summary_parts else "Material knowledge summary unavailable.",
                "phases": [getattr(mk, "material_label", None)] if mk is not None else [],
                "structures": [getattr(mk, "crystal_structure", None)] if mk is not None else [],
                "mechanisms": mechanisms,
                "required_model_features": _required_model_features(state),
                "unknowns": unknowns,
            }
            return append_trace(updated, "material_knowledge_agent", "material_knowledge_compiled", {
                "unknown_count": len(updated["material_knowledge"]["unknowns"]),
            })

    return _MaterialKnowledgeWrapper()


def _run_simulation_planner(agent: SimulationPlannerAgent):
    class _SimulationPlannerWrapper:
        def run(self, state: MaterialsResearchState) -> MaterialsResearchState:
            legacy_state = legacy_state_from_materials_state(state)
            updated_legacy = agent.run(legacy_state)
            plan = updated_legacy.simulation_plan
            strategy = dict(state.get("modeling_strategy") or {})
            research_case = dict(state.get("research_case") or {})
            if plan is None:
                raise ValueError("Simulation planner did not produce a SimulationPlan.")
            if strategy.get("simulation_abstraction") == "single_crystal":
                plan.geometry.grains = 1
            planned_target_grains = strategy.get("target_grains")
            if isinstance(planned_target_grains, int) and planned_target_grains != plan.geometry.grains:
                strategy["recommended_follow_on_grains"] = max(planned_target_grains, plan.geometry.grains)
                strategy["target_grains"] = plan.geometry.grains
                assumptions = list(strategy.get("assumptions", []))
                adjustment_note = (
                    f"The current executable plan uses {plan.geometry.grains} grains as a conservative first pass; "
                    f"a broader follow-on target of {strategy['recommended_follow_on_grains']} grains remains recommended."
                )
                if adjustment_note not in assumptions:
                    assumptions.append(adjustment_note)
                strategy["assumptions"] = assumptions
            plan.outputs = sorted(set(list(plan.outputs) + list(strategy.get("required_outputs", []))))
            plan.loading.mode = research_case.get("loading_mode", plan.loading.mode)
            plan.summary = (
                f"{plan.summary} Strategy={strategy.get('simulation_abstraction', 'unspecified')}; "
                f"comparison_targets={strategy.get('comparison_targets', [])}"
            )
            updated_legacy.simulation_plan = plan
            updated = materials_state_from_legacy(state, updated_legacy)
            updated["modeling_strategy"] = strategy
            return append_trace(updated, "simulation_planner", "simulation_plan_compiled", {
                "plan_name": plan.name,
                "outputs": plan.outputs,
            })

    return _SimulationPlannerWrapper()


def _run_scientific_critic(agent: ScientificCriticAgent):
    class _ScientificCriticWrapper:
        def run(self, state: MaterialsResearchState) -> MaterialsResearchState:
            legacy_state = legacy_state_from_materials_state(state)
            updated_legacy = agent.run(legacy_state)
            updated = materials_state_from_legacy(state, updated_legacy)
            critic = updated_legacy.critic_report
            alignment = dict(state.get("alignment_report") or {})
            hypotheses = list(state.get("hypotheses", []))
            if critic is not None:
                if hypotheses:
                    critic.limitations.append("Hypotheses remain provisional until experiment-simulation alignment is demonstrated.")
                if alignment.get("status") == "comparison_not_possible":
                    critic.limitations.append("Experiment-simulation comparison could not be completed from the current data products.")
                if alignment.get("notes"):
                    for item in alignment["notes"]:
                        if item not in critic.next_steps:
                            critic.next_steps.append(item)
                updated["critic_report"] = critic
            return append_trace(updated, "scientific_critic", "scientific_critique_compiled", {
                "has_alignment": bool(alignment),
                "hypothesis_count": len(hypotheses),
            })

    return _ScientificCriticWrapper()


def _infer_loading_mode(query: str, objective: str) -> str:
    lowered = f"{query} {objective}".lower()
    if "cyclic" in lowered:
        return "cyclic_loading"
    if "shear" in lowered:
        return "simple_shear"
    if "rolling" in lowered:
        return "plane_strain_rolling_proxy"
    if "compression" in lowered:
        return "uniaxial_compression"
    return "uniaxial_tension"


def _infer_microstructure(query: str) -> str:
    lowered = query.lower()
    if "single crystal" in lowered or "single-crystal" in lowered:
        return "single_crystal"
    return "polycrystal"


def _infer_structure(query: str, material_system: str) -> str:
    lowered = f"{query} {material_system}".lower()
    if "l12" in lowered:
        return "L12"
    if "bcc" in lowered:
        return "bcc"
    if "hcp" in lowered:
        return "hcp"
    return "fcc"


def _requires_complex_loading(query: str) -> bool:
    lowered = query.lower()
    return any(token in lowered for token in ("rolling", "cyclic", "path change", "multiaxial"))


def _build_research_questions(user_query: str, research_case: dict[str, Any]) -> list[str]:
    questions = [
        f"What DAMASK abstraction is appropriate for {research_case['material_system']} under {research_case['loading_mode']}?",
        "Which observables can be compared against literature or experiment?",
    ]
    if research_case.get("has_experimental_data"):
        questions.append("How should simulation outputs be aligned with the provided experimental datasets?")
    else:
        questions.append("What assumptions are required in the absence of experimental data?")
    if "texture" in user_query.lower():
        questions.append("How should texture or orientation information be represented?")
    return questions


def _extract_mechanisms(summary: str) -> list[str]:
    lowered = summary.lower()
    mechanisms = []
    if "slip" in lowered:
        mechanisms.append("slip")
    if "twinning" in lowered:
        mechanisms.append("twinning")
    if "hardening" in lowered:
        mechanisms.append("hardening")
    return mechanisms


def _extract_model_hints(summary: str) -> list[str]:
    lowered = summary.lower()
    hints = []
    if "phenopowerlaw" in lowered:
        hints.append("phenopowerlaw")
    if "viscoplastic" in lowered:
        hints.append("viscoplastic")
    return hints


def _extract_reported_parameters(evidence_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _ = evidence_items
    return []


def _extract_experimental_conditions(notes: list[str]) -> list[str]:
    conditions: list[str] = []
    for note in notes:
        lowered = note.lower()
        if "tension" in lowered:
            conditions.append("uniaxial_tension")
        if "compression" in lowered:
            conditions.append("uniaxial_compression")
        if "temperature" in lowered:
            conditions.append("temperature_noted")
    return sorted(set(conditions))


def _extract_validation_observables(notes: list[str]) -> list[str]:
    observables: list[str] = []
    for note in notes:
        lowered = note.lower()
        if "stress" in lowered:
            observables.append("stress")
        if "strain" in lowered:
            observables.append("strain")
        if "texture" in lowered:
            observables.append("texture")
        if "hardness" in lowered:
            observables.append("hardness")
    return sorted(set(observables))


def _normalize_literature_sources(
    *,
    provided_sources: list[str],
    resolved_sources: list[str],
    user_query: str,
) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for source in list(provided_sources) + list(resolved_sources):
        canonical = _canonicalize_source_label(source, user_query)
        if not canonical:
            continue
        key = canonical.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(canonical)
    return normalized


def _canonicalize_source_label(source: Any, user_query: str) -> str | None:
    text = str(source).strip()
    if not text:
        return None
    lowered = text.lower()
    if lowered == user_query.strip().lower():
        return None
    doi_match = __import__("re").search(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", text, __import__("re").IGNORECASE)
    if doi_match:
        return f"DOI:{doi_match.group(0)}"
    arxiv_match = __import__("re").search(r"(?:arxiv:)?(\d{4}\.\d{4,5}(?:v\d+)?)", text, __import__("re").IGNORECASE)
    if arxiv_match:
        return f"ARXIV:{arxiv_match.group(1)}"
    return text


def _required_model_features(state: MaterialsResearchState) -> list[str]:
    research_case = dict(state.get("research_case") or {})
    features = ["finite_strain", "crystal_plasticity"]
    if research_case.get("loading_mode") == "cyclic_loading":
        features.append("history_dependent_loading")
    if research_case.get("microstructure") == "polycrystal":
        features.append("orientation_distribution")
    return features


def _slugify(value: str) -> str:
    return "_".join(part for part in "".join(ch.lower() if ch.isalnum() else "_" for ch in value).split("_") if part)


def _is_graph_interrupt(exc: Exception) -> bool:
    return type(exc).__name__ in {"GraphInterrupt", "NodeInterrupt"}
