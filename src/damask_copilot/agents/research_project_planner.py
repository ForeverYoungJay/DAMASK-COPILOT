"""Project-level research planner agent."""

from __future__ import annotations

import json
from typing import Any

from damask_copilot.graph.materials_research_state import MaterialsResearchState, append_trace
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.project_plan import (
    CandidateSimulation,
    EvidenceStatus,
    ProjectMilestone,
    ProjectPlan,
)


class ResearchProjectPlannerAgent:
    """Create a staged project roadmap before concrete DAMASK planning."""

    name = "research_project_planner"
    category = "cognitive"
    uses_llm = True

    def __init__(
        self,
        *,
        use_llm: bool = False,
        model_name: str | None = None,
        llm_runner: StructuredLLMRunner | None = None,
    ) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state: MaterialsResearchState) -> MaterialsResearchState:
        if self.use_llm or state.get("use_llm", False):
            return self._run_llm(state)
        return self._run_deterministic(state)

    def _run_llm(self, state: MaterialsResearchState) -> MaterialsResearchState:
        runner = self.llm_runner or StructuredLLMRunner(model_name=state.get("model") or self.model_name)
        parsed = runner.run_structured(
            prompt_name="research_project_planner",
            system_prompt=load_prompt("research_project_planner"),
            user_prompt=(
                f"User query: {state.get('user_query')}\n"
                f"Research case: {json.dumps(state.get('research_case') or {}, ensure_ascii=False)}\n"
                f"Research questions: {json.dumps(state.get('research_questions') or [], ensure_ascii=False)}\n"
                f"Literature review: {json.dumps(state.get('literature_review') or {}, ensure_ascii=False)}\n"
                f"Experimental data summary: {json.dumps(state.get('experimental_data_summary') or {}, ensure_ascii=False)}\n"
                f"Material knowledge: {json.dumps(state.get('material_knowledge') or {}, ensure_ascii=False)}\n"
                f"Hypotheses: {json.dumps(state.get('hypotheses') or [], ensure_ascii=False)}\n"
                f"Modeling strategy: {json.dumps(state.get('modeling_strategy') or {}, ensure_ascii=False)}\n"
                f"Parameter card: {json.dumps(self._jsonable(state.get('parameter_card')), ensure_ascii=False)}\n"
                f"Human feedback history: {json.dumps(state.get('human_feedback_history') or [], ensure_ascii=False)}\n"
                f"Safety constraints: {json.dumps(self._safety_constraints(state), ensure_ascii=False)}"
            ),
            output_schema=ProjectPlan,
            model_name=state.get("model") or self.model_name,
        )
        return self._store_plan(state, parsed, trace_event="project_plan_defined_llm")

    def _run_deterministic(self, state: MaterialsResearchState) -> MaterialsResearchState:
        research_case = dict(state.get("research_case") or {})
        literature = dict(state.get("literature_review") or {})
        experimental = dict(state.get("experimental_data_summary") or {})
        material_knowledge = dict(state.get("material_knowledge") or {})
        modeling_strategy = dict(state.get("modeling_strategy") or {})
        parameter_card = self._jsonable(state.get("parameter_card")) or {}
        hypotheses = list(state.get("hypotheses") or [])
        research_questions = list(state.get("research_questions") or [])
        safety_constraints = self._safety_constraints(state)

        objective = str(research_case.get("objective") or state.get("user_query") or "Define a credible materials research roadmap.")
        if not research_questions:
            research_questions = [
                f"What mechanism most plausibly controls {research_case.get('loading_mode', 'the target response')}?",
                "What evidence is already available, and what remains assumed?",
            ]

        evidence_status = [
            self._literature_evidence(literature),
            self._experimental_evidence(experimental),
            self._parameter_evidence(parameter_card),
        ]
        if safety_constraints:
            evidence_status.append(
                EvidenceStatus(
                    topic="Safety and execution constraints",
                    status="supported",
                    evidence_summary="Explicit execution and safety constraints were provided and must remain binding during downstream planning.",
                    supporting_items=[str(item) for item in safety_constraints],
                    assumptions=[],
                )
            )

        deliverables = [
            "Project-level research roadmap that separates evidence-backed findings from assumptions.",
            "Prioritized candidate simulation list for DAMASK execution planning.",
            "Review-ready summary of evidence gaps, risks, and success criteria.",
        ]
        comparison_targets = list(modeling_strategy.get("comparison_targets", []) or [])
        if comparison_targets:
            deliverables.append(f"Validation matrix for {', '.join(comparison_targets)}.")

        milestone_1 = ProjectMilestone(
            milestone_id="M1",
            title="Consolidate evidence baseline",
            description="Confirm what the literature and experimental datasets actually support before committing to specific simulations.",
            evidence_needed=[
                "Literature-backed mechanisms or constitutive guidance.",
                "Experimental metadata sufficient for later comparison.",
            ],
            deliverables=["Evidence map", "Open assumptions list"],
            review_required=bool(literature.get("unsupported_claims") or experimental.get("needs_human_correction")),
        )
        milestone_2 = ProjectMilestone(
            milestone_id="M2",
            title="Select screening simulation path",
            description="Choose a first executable DAMASK study that best reduces the highest-priority uncertainty.",
            evidence_needed=[
                "Modeling abstraction consistent with the research question.",
                "A candidate simulation tied to at least one hypothesis or validation target.",
            ],
            deliverables=["Selected candidate simulation", "Simulation planning brief"],
            review_required=True,
        )
        milestone_3 = ProjectMilestone(
            milestone_id="M3",
            title="Define validation and iteration criteria",
            description="State how success will be judged and where the next iteration should branch if evidence remains weak.",
            evidence_needed=[
                "Clear success criteria.",
                "Human review checkpoints for low-confidence assumptions.",
            ],
            deliverables=["Success criteria checklist", "Iteration triggers"],
            review_required=True,
        )

        candidate_simulations = self._build_candidate_simulations(
            research_case=research_case,
            hypotheses=hypotheses,
            modeling_strategy=modeling_strategy,
            experimental=experimental,
        )
        if not candidate_simulations:
            candidate_simulations = [
                CandidateSimulation(
                    simulation_id="SIM-1",
                    title="Baseline screening simulation",
                    objective="Establish a first DAMASK baseline aligned with the current research objective.",
                    why_needed="A baseline executable plan is needed before any calibration or hypothesis discrimination is possible.",
                    target_hypotheses=[],
                    required_evidence=["Research objective", "Modeling abstraction"],
                    simulation_type_hint=str(research_case.get("loading_mode") or modeling_strategy.get("loading_proxy") or "uniaxial_tension"),
                    priority=1,
                )
            ]

        human_review_points = list(dict(modeling_strategy).get("limitations", [])[:1])
        if literature.get("unsupported_claims"):
            human_review_points.append("Verify unsupported literature claims before using them as parameter or mechanism evidence.")
        if experimental.get("needs_human_correction"):
            human_review_points.append("Resolve experimental metadata ambiguities before claiming quantitative agreement.")
        parameter_flags = list(parameter_card.get("parameters", {}).get("review_flags", []) or [])
        if parameter_flags:
            human_review_points.append(f"Confirm whether current parameter-card review flags are acceptable for screening: {parameter_flags}.")
        if not human_review_points:
            human_review_points.append("Confirm that the first candidate simulation is the right next step for this project.")

        risks = []
        risks.extend(str(item) for item in literature.get("evidence_gaps", [])[:2])
        risks.extend(str(item) for item in experimental.get("metadata_questions", [])[:2])
        if parameter_flags:
            risks.append("Parameter confidence remains limited, so simulation outcomes may be suitable only for screening.")
        if safety_constraints:
            risks.append("Execution must respect the provided safety constraints and approval boundaries.")
        if not risks:
            risks.append("Evidence remains incomplete, so project conclusions should stay provisional until targeted simulations are reviewed.")

        success_criteria = [
            "At least one candidate simulation is clearly linked to the project objective and a testable hypothesis.",
            "The plan explicitly distinguishes evidence-backed statements from assumptions.",
            "Human review points are identified before executable DAMASK inputs are generated.",
        ]
        if comparison_targets:
            success_criteria.append(f"A downstream simulation can be evaluated against {', '.join(comparison_targets)}.")

        plan = ProjectPlan(
            project_objective=objective,
            research_questions=research_questions,
            evidence_status=evidence_status,
            milestones=[milestone_1, milestone_2, milestone_3],
            deliverables=deliverables,
            candidate_simulations=candidate_simulations,
            human_review_points=human_review_points,
            risks=risks,
            success_criteria=success_criteria,
            next_action="human_review_framing" if human_review_points else "simulation_planner",
        )
        return self._store_plan(state, plan, trace_event="project_plan_defined")

    def _store_plan(self, state: MaterialsResearchState, plan: ProjectPlan, *, trace_event: str) -> MaterialsResearchState:
        updated = dict(state)
        updated["project_plan"] = plan
        updated["project_milestones"] = [item.milestone_id for item in plan.milestones]
        updated["current_milestone"] = plan.milestones[0].milestone_id if plan.milestones else None
        updated["candidate_simulations"] = plan.candidate_simulations
        updated["selected_simulation_id"] = (
            state.get("selected_simulation_id")
            or (plan.candidate_simulations[0].simulation_id if plan.candidate_simulations else None)
        )
        return append_trace(
            updated,
            self.name,
            trace_event,
            {
                "milestones": len(plan.milestones),
                "candidate_simulations": len(plan.candidate_simulations),
                "next_action": plan.next_action,
            },
        )

    def _build_candidate_simulations(
        self,
        *,
        research_case: dict[str, Any],
        hypotheses: list[dict[str, Any]],
        modeling_strategy: dict[str, Any],
        experimental: dict[str, Any],
    ) -> list[CandidateSimulation]:
        candidates: list[CandidateSimulation] = []
        loading_hint = str(research_case.get("loading_mode") or modeling_strategy.get("loading_proxy") or "uniaxial_tension")
        observables = list(experimental.get("observable_candidates", []) or [])
        abstraction = str(modeling_strategy.get("simulation_abstraction") or "screening_rve")
        for index, hypothesis in enumerate(hypotheses[:3], start=1):
            hypothesis_id = str(hypothesis.get("id") or f"H{index}")
            observable = str(hypothesis.get("expected_observable") or (observables[0] if observables else "stress_strain_curve"))
            candidates.append(
                CandidateSimulation(
                    simulation_id=f"SIM-{index}",
                    title=f"{hypothesis_id} screening study",
                    objective=str(hypothesis.get("statement") or f"Test {hypothesis_id}."),
                    why_needed=f"Needed to test {hypothesis_id} against the observable {observable} using a {abstraction} abstraction.",
                    target_hypotheses=[hypothesis_id],
                    required_evidence=[observable] if observable else [],
                    simulation_type_hint=loading_hint,
                    priority=index,
                )
            )
        return candidates

    @staticmethod
    def _literature_evidence(literature: dict[str, Any]) -> EvidenceStatus:
        supported = list(literature.get("mechanisms", []) or []) + list(literature.get("planning_implications", []) or [])
        assumptions = list(literature.get("unsupported_claims", []) or [])
        if literature.get("status") == "literature_missing":
            status = "missing"
            summary = "No literature review was available, so mechanism and modeling guidance remain assumption-heavy."
        elif assumptions:
            status = "partial"
            summary = "Literature context exists, but some claims still require verification before they guide quantitative planning."
        else:
            status = "supported" if supported else "partial"
            summary = literature.get("summary") or "Literature review was provided but remains qualitative."
        return EvidenceStatus(
            topic="Literature and mechanism basis",
            status=status,
            evidence_summary=str(summary),
            supporting_items=[str(item) for item in supported[:4]],
            assumptions=[str(item) for item in assumptions[:4]],
        )

    @staticmethod
    def _experimental_evidence(experimental: dict[str, Any]) -> EvidenceStatus:
        observables = [str(item) for item in experimental.get("observable_candidates", []) or []]
        assumptions = [str(item) for item in experimental.get("metadata_questions", []) or []]
        if experimental.get("status") == "experimental_data_missing":
            status = "missing"
            summary = "No experimental dataset is currently available for validation."
        elif experimental.get("needs_human_correction"):
            status = "partial"
            summary = experimental.get("summary") or "Experimental data exist but require metadata clarification before quantitative use."
        else:
            status = "supported" if observables else "partial"
            summary = experimental.get("summary") or "Experimental data summary is available."
        return EvidenceStatus(
            topic="Experimental evidence and validation readiness",
            status=status,
            evidence_summary=str(summary),
            supporting_items=observables,
            assumptions=assumptions,
        )

    @staticmethod
    def _parameter_evidence(parameter_card: dict[str, Any]) -> EvidenceStatus:
        parameters = dict(parameter_card.get("parameters") or {})
        review_flags = [str(item) for item in parameters.get("review_flags", []) or []]
        confidence = str(parameter_card.get("confidence") or parameters.get("effective_confidence") or "unknown")
        if not parameter_card:
            status = "missing"
            summary = "No parameter card is available yet."
        elif review_flags:
            status = "partial"
            summary = f"Parameter card exists with confidence={confidence}, but review flags remain open."
        else:
            status = "supported"
            summary = f"Parameter card exists with confidence={confidence} and no explicit review flags."
        return EvidenceStatus(
            topic="Parameter readiness",
            status=status,
            evidence_summary=summary,
            supporting_items=[f"confidence={confidence}"],
            assumptions=review_flags,
        )

    @staticmethod
    def _jsonable(value: Any) -> Any:
        if value is None:
            return None
        dumper = getattr(value, "model_dump", None)
        if dumper is not None:
            return dumper()
        if hasattr(value, "dict"):
            return value.dict()
        return value

    @staticmethod
    def _safety_constraints(state: MaterialsResearchState) -> list[Any]:
        constraints = dict(state.get("user_constraints") or {})
        safety = constraints.get("safety_constraints")
        if isinstance(safety, list):
            return list(safety)
        if safety is None:
            return []
        return [safety]
