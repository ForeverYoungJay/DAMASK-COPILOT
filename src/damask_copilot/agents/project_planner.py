"""Project planning agent for the v1 workflow."""

from __future__ import annotations

import json
from typing import Any

from damask_copilot.graph.state import ResearchState
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.policies.simulation_budget import MAX_TOTAL_CELLS
from damask_copilot.schemas.llm_outputs import ProjectPlannerOutput


class ProjectPlannerAgent:
    """Create a project-level scientific plan from goals, evidence, priors, and budget."""

    name = "project_planner"

    def __init__(self, *, use_llm: bool = False, model_name: str | None = None, llm_runner=None) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state: ResearchState) -> ResearchState:
        literature = state.literature_summary or {}
        planning_evidence = dict(literature.get("planning_evidence") or {})
        experimental = state.experimental_data or {}
        known_parameters = state.known_parameters or {}
        damask_capabilities = state.damask_capabilities or {}
        workflow_type = state.workflow_type or "simulation_run"
        material_system = state.material_system or "the target material"

        validation_metrics = self._validation_metrics(experimental, workflow_type)
        evidence_status = self._evidence_status(literature, experimental, known_parameters, damask_capabilities)
        compute_budget = self._compute_budget(state)
        project_context = self._project_context(state, literature, experimental)
        parameter_priors = self._parameter_priors(known_parameters, damask_capabilities)
        llm_plan = self._run_llm_plan(
            state=state,
            workflow_type=workflow_type,
            material_system=material_system,
            project_context=project_context,
            parameter_priors=parameter_priors,
            evidence_status=evidence_status,
            compute_budget=compute_budget,
            damask_capabilities=damask_capabilities,
        )
        project_objective = llm_plan.project_objective or state.objective or state.user_goal
        research_questions = list(llm_plan.research_questions)
        hypotheses = [item.model_dump() for item in llm_plan.hypotheses]
        evidence_status = [item.model_dump() for item in llm_plan.evidence_status] if llm_plan.evidence_status else evidence_status
        validation_metrics = list(llm_plan.validation_metrics) or validation_metrics
        candidate_simulations = [item.model_dump() for item in llm_plan.candidate_simulations]
        stopping_criteria = list(llm_plan.stopping_criteria) or self._stopping_criteria(
            workflow_type=workflow_type,
            state=state,
            validation_metrics=validation_metrics,
        )
        calibration_strategy = dict(llm_plan.calibration_strategy or {}) or self._calibration_strategy(workflow_type, validation_metrics, state)
        iteration_logic = list(llm_plan.iteration_logic) or self._iteration_logic(workflow_type)
        risks = list(llm_plan.risks) or self._risks(literature, experimental, known_parameters, compute_budget)
        deliverables = list(llm_plan.deliverables) or [
            "Scientific project roadmap",
            "Testable hypotheses linked to validation metrics",
            "Candidate DAMASK simulation plan outline",
        ]
        next_action = llm_plan.next_action or ("simulation_designer" if state.needs_damask_simulation else "research_report")

        state.hypotheses = hypotheses

        state.project_plan = {
            "project_objective": project_objective,
            "workflow_type": workflow_type,
            "material_system": material_system,
            "project_context": project_context,
            "parameter_priors": parameter_priors,
            "research_questions": research_questions,
            "evidence_status": evidence_status,
            "validation_metrics": validation_metrics,
            "calibration_strategy": calibration_strategy,
            "candidate_simulations": candidate_simulations,
            "compute_budget": compute_budget,
            "damask_constraints": self._damask_constraints(damask_capabilities),
            "parameter_strategy": self._parameter_strategy(known_parameters, state),
            "stopping_criteria": stopping_criteria,
            "iteration_logic": iteration_logic,
            "deliverables": deliverables,
            "risks": risks,
            "next_action": next_action,
            "literature_gaps": literature.get("evidence_gaps", []),
        }
        return state.append_trace(
            self.name,
            "project_plan_created",
            {
                "hypothesis_count": len(state.hypotheses),
                "candidate_simulation_count": len(candidate_simulations),
                "workflow_type": workflow_type,
            },
        )

    def _run_llm_plan(
        self,
        *,
        state: ResearchState,
        workflow_type: str,
        material_system: str,
        project_context: dict[str, Any],
        parameter_priors: dict[str, Any],
        evidence_status: list[dict[str, Any]],
        compute_budget: dict[str, Any],
        damask_capabilities: dict[str, Any],
    ) -> ProjectPlannerOutput | None:
        try:
            runner = self.llm_runner or StructuredLLMRunner(model_name=state.model or self.model_name)
            return runner.run_structured(
                prompt_name="project_planner",
                system_prompt=load_prompt("project_planner"),
                user_prompt=(
                    f"User goal: {state.user_goal}\n"
                    f"Workflow type: {workflow_type}\n"
                    f"Material system: {material_system}\n"
                    f"Project context: {json.dumps(project_context, ensure_ascii=False)}\n"
                    f"Literature summary: {json.dumps(state.literature_summary or {}, ensure_ascii=False)}\n"
                    f"Experimental data: {json.dumps(state.experimental_data or {}, ensure_ascii=False)}\n"
                    f"Known parameters: {json.dumps(state.known_parameters or {}, ensure_ascii=False)}\n"
                    f"Parameter priors: {json.dumps(parameter_priors, ensure_ascii=False)}\n"
                    f"DAMASK capabilities: {json.dumps(damask_capabilities, ensure_ascii=False)}\n"
                    f"Evidence status: {json.dumps(evidence_status, ensure_ascii=False)}\n"
                    f"Compute budget: {json.dumps(compute_budget, ensure_ascii=False)}\n"
                    f"Current iteration: {state.iteration}\n"
                    f"Max iterations: {state.max_iterations}\n"
                    "Return a scientific project plan. Do not use generic placeholder research questions or hypotheses."
                ),
                output_schema=ProjectPlannerOutput,
                model_name=state.model or self.model_name,
            )
        except Exception as exc:
            raise RuntimeError(
                "ProjectPlannerAgent is now LLM-only. Configure a working LLM runner or enable mock structured outputs."
            ) from exc

    def _project_context(
        self,
        state: ResearchState,
        literature: dict[str, Any],
        experimental: dict[str, Any],
    ) -> dict[str, Any]:
        experimental_curve = experimental.get("curve")
        datasets = list(experimental.get("datasets", []) or [])
        return {
            "project_name": state.project_name,
            "project_dir": state.project_dir,
            "user_files": list(state.user_files),
            "literature_files": list(state.literature_files),
            "experimental_files": list(state.experimental_files),
            "literature_sources": list(state.literature_sources),
            "project_evidence": {
                "literature_summary": literature.get("summary"),
                "literature_mechanisms": list(literature.get("mechanisms", [])),
                "literature_planning_evidence": dict(literature.get("planning_evidence") or {}),
                "experimental_summary": experimental.get("summary"),
                "experimental_conditions": list(experimental.get("experimental_conditions", [])),
                "experimental_observables": list(experimental.get("observable_candidates", [])),
                "has_experimental_curve": bool(experimental_curve),
                "dataset_count": len(datasets),
            },
            "context_policy": "Project-specific context should come from projects/<project_name>/ or explicitly attached project files.",
        }

    def _parameter_priors(self, known_parameters: dict[str, Any], damask_capabilities: dict[str, Any]) -> dict[str, Any]:
        memory_context = dict(known_parameters.get("scientific_memory_context") or {})
        cp_database = dict(memory_context.get("cp_parameter_database") or {})
        demo_source = known_parameters.get("source") or cp_database.get("source_path")
        return {
            "parameter_source": known_parameters.get("source"),
            "database_record": cp_database,
            "reported_cp_parameters": dict(known_parameters.get("reported_cp_parameters", {})),
            "elastic_constants": dict(known_parameters.get("elastic_constants", {})),
            "phase_information": dict(known_parameters.get("phase_information", {})),
            "materials_knowledge_graph_hits": list(known_parameters.get("materials_knowledge_graph_hits", [])),
            "damask_documentation_sources": list(damask_capabilities.get("documentation_sources", [])),
            "data_policy": {
                "current_mode": "demo_dataset",
                "demo_dataset_root": "data/materials",
                "future_backend": "sql_database",
                "note": "Parameter priors are infrastructure data and should remain separate from project folders.",
            },
            "demo_dataset_source": demo_source,
        }

    def _research_questions(
        self,
        state: ResearchState,
        literature: dict[str, Any],
        planning_evidence: dict[str, Any],
        experimental: dict[str, Any],
        known_parameters: dict[str, Any],
    ) -> list[str]:
        questions = [state.user_goal]
        if state.workflow_type == "calibration":
            questions.append("Which CP parameters most strongly control the target observables?")
        if planning_evidence.get("mechanisms") or literature.get("mechanisms"):
            questions.append(f"Which literature-supported mechanisms best explain the response of {state.material_system or 'the material'}?")
        observables = list(planning_evidence.get("observables_for_validation", [])) or list(experimental.get("observable_candidates", []))
        if observables:
            questions.append(f"Which observable should be prioritized for validation: {observables[0]}?")
        if known_parameters.get("phase_information"):
            phase = known_parameters["phase_information"].get("phase_name") or state.material_system
            questions.append(f"What constitutive assumptions are justified for phase {phase}?")
        return questions

    def _validation_metrics(self, experimental: dict[str, Any], workflow_type: str) -> list[str]:
        metrics = list(experimental.get("observable_candidates", []) or [])
        if not metrics and experimental.get("curve"):
            metrics = ["stress_strain_curve"]
        if not metrics:
            metrics = ["stress_strain_curve", "yield_stress", "hardening_rate"] if workflow_type == "calibration" else ["stress_strain_curve"]
        return metrics

    def _hypotheses(
        self,
        *,
        state: ResearchState,
        literature: dict[str, Any],
        planning_evidence: dict[str, Any],
        experimental: dict[str, Any],
        known_parameters: dict[str, Any],
        validation_metrics: list[str],
    ) -> list[dict[str, Any]]:
        evidence = list(planning_evidence.get("mechanisms", [])[:2]) or list(literature.get("mechanisms", [])[:2]) or [
            literature.get("summary", "Planning hypothesis derived from the user goal.")
        ]
        material_name = known_parameters.get("material_name") or state.material_system or "the target material"
        phase_name = dict(known_parameters.get("phase_information") or {}).get("phase_name")
        hypotheses = [
            {
                "id": "H1",
                "statement": (
                    f"A DAMASK model for {material_name} can reproduce the dominant requested response "
                    f"under the chosen loading path using the current constitutive assumptions."
                ),
                "evidence": evidence,
                "validation_metric": validation_metrics[0],
                "type": "baseline_reproducibility",
            }
        ]
        if state.workflow_type == "calibration":
            hypotheses.append(
                {
                    "id": "H2",
                    "statement": (
                        "Adjusting crystal-plasticity hardening and strength parameters will improve agreement "
                        "with the target experimental stress-strain response."
                    ),
                    "evidence": [experimental.get("summary", "Experimental response available for calibration."), known_parameters.get("source", "parameter_priors")],
                    "validation_metric": validation_metrics[0],
                    "type": "parameter_calibration",
                }
            )
        if phase_name:
            hypotheses.append(
                {
                    "id": "H3",
                    "statement": f"The active response is controlled primarily by phase {phase_name} and its slip-system assumptions.",
                    "evidence": [phase_name, known_parameters.get("phase_information", {})],
                    "validation_metric": validation_metrics[0],
                    "type": "phase_mechanism",
                }
            )
        return hypotheses

    def _evidence_status(
        self,
        literature: dict[str, Any],
        experimental: dict[str, Any],
        known_parameters: dict[str, Any],
        damask_capabilities: dict[str, Any],
    ) -> list[dict[str, Any]]:
        return [
            {
                "topic": "literature",
                "status": self._status_from_presence(literature.get("summary"), gaps=literature.get("evidence_gaps", [])),
                "summary": literature.get("summary", "No literature summary available."),
            },
            {
                "topic": "experimental_data",
                "status": self._status_from_presence(experimental.get("summary"), gaps=experimental.get("metadata_questions", [])),
                "summary": experimental.get("summary", "No experimental summary available."),
            },
            {
                "topic": "cp_parameters",
                "status": self._status_from_presence(known_parameters.get("reported_cp_parameters"), gaps=[]),
                "summary": known_parameters.get("source", "No parameter source available."),
            },
            {
                "topic": "damask_capabilities",
                "status": self._status_from_presence(damask_capabilities.get("preprocess_tools"), gaps=[]),
                "summary": "DAMASK capability package assembled for planning.",
            },
        ]

    def _compute_budget(self, state: ResearchState) -> dict[str, Any]:
        if state.mode == "dry_run":
            recommended_cells = [8, 8, 8]
            recommended_grains = 4
        elif state.mode == "smoke_test":
            recommended_cells = [16, 16, 16]
            recommended_grains = 8
        else:
            recommended_cells = [24, 24, 24]
            recommended_grains = 16
        total_cells = recommended_cells[0] * recommended_cells[1] * recommended_cells[2]
        return {
            "mode": state.mode,
            "max_total_cells": MAX_TOTAL_CELLS,
            "recommended_cells": recommended_cells,
            "recommended_grains": recommended_grains,
            "recommended_total_cells": total_cells,
            "within_budget": total_cells <= MAX_TOTAL_CELLS,
            "notes": "Project planning should stay within deterministic smoke-test budget unless explicitly escalated.",
        }

    def _candidate_simulations(
        self,
        *,
        workflow_type: str,
        material_system: str,
        hypotheses: list[dict[str, Any]],
        validation_metrics: list[str],
    ) -> list[dict[str, Any]]:
        simulation_type_hint = "parameter_calibration" if workflow_type == "calibration" else workflow_type
        candidates: list[dict[str, Any]] = []
        for index, hypothesis in enumerate(hypotheses[:3], start=1):
            candidates.append(
                {
                    "simulation_id": f"SIM-{index}",
                    "title": f"{material_system} study {index}",
                    "objective": hypothesis["statement"],
                    "why_needed": f"Needed to test {hypothesis['id']} against {hypothesis['validation_metric']}.",
                    "target_hypotheses": [hypothesis["id"]],
                    "required_evidence": validation_metrics[:2],
                    "simulation_type_hint": simulation_type_hint,
                    "priority": index,
                }
            )
        return candidates

    def _stopping_criteria(self, *, workflow_type: str, state: ResearchState, validation_metrics: list[str]) -> list[str]:
        criteria = [
            "Stop when the critique recommends stop.",
            f"Stop when max_iterations ({state.max_iterations}) is reached.",
        ]
        if workflow_type == "calibration":
            criteria.append(f"Stop when the chosen validation metrics ({', '.join(validation_metrics)}) are judged sufficiently matched.")
        else:
            criteria.append("Stop when the planned simulation evidence is sufficient to answer the main scientific question.")
        return criteria

    def _calibration_strategy(self, workflow_type: str, validation_metrics: list[str], state: ResearchState) -> dict[str, Any]:
        if workflow_type != "calibration":
            return {
                "enabled": False,
                "objective": "Prioritize physically reasonable parameter choices before quantitative fitting.",
            }
        return {
            "enabled": True,
            "objective": "Tune CP parameters against experimental observables.",
            "target_metrics": validation_metrics,
            "optimization_focus": (
                "Prioritize strength and hardening parameters first."
                if state.needs_parameter_optimization
                else "Use reported literature parameters as fixed priors."
            ),
        }

    def _damask_constraints(self, damask_capabilities: dict[str, Any]) -> dict[str, Any]:
        return {
            "available_preprocess_tools": list(damask_capabilities.get("preprocess_tools", [])),
            "available_execution_tools": list(damask_capabilities.get("execution_tools", [])),
            "available_postprocess_tools": list(damask_capabilities.get("postprocess_tools", [])),
            "documentation_sources": list(damask_capabilities.get("documentation_sources", [])),
        }

    def _parameter_strategy(self, known_parameters: dict[str, Any], state: ResearchState) -> dict[str, Any]:
        return {
            "parameter_source": known_parameters.get("source"),
            "has_reported_cp_parameters": bool(known_parameters.get("reported_cp_parameters")),
            "has_elastic_constants": bool(known_parameters.get("elastic_constants")),
            "needs_parameter_optimization": state.needs_parameter_optimization,
        }

    def _iteration_logic(self, workflow_type: str) -> list[str]:
        if workflow_type == "calibration":
            return [
                "Design a conservative baseline simulation.",
                "Validate DAMASK inputs and execute.",
                "Compare simulation against experiment and update parameters if mismatch remains large.",
            ]
        return [
            "Design a baseline simulation aligned with the leading hypothesis.",
            "Validate and execute the simulation.",
            "Critique the result and iterate only if scientific uncertainty remains high.",
        ]

    def _risks(
        self,
        literature: dict[str, Any],
        experimental: dict[str, Any],
        known_parameters: dict[str, Any],
        compute_budget: dict[str, Any],
    ) -> list[str]:
        risks: list[str] = []
        risks.extend(str(item) for item in (literature.get("evidence_gaps", []) or [])[:2])
        risks.extend(str(item) for item in (experimental.get("metadata_questions", []) or [])[:2])
        if known_parameters.get("confidence") in {"low", "unknown"}:
            risks.append("Known CP parameters are low-confidence and may only be suitable as priors.")
        if not compute_budget.get("within_budget", True):
            risks.append("Recommended project budget exceeds the deterministic execution ceiling.")
        if not risks:
            risks.append("Project conclusions remain provisional until simulation and critique close the evidence gaps.")
        return risks

    @staticmethod
    def _status_from_presence(payload: Any, *, gaps: list[Any]) -> str:
        if not payload:
            return "missing"
        if gaps:
            return "partial"
        return "supported"
