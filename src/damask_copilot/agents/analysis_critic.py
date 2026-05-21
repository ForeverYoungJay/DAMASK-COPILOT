"""Unified analysis and critique agent for the v1 DAMASK workflow."""

from __future__ import annotations

from typing import Any

from damask_copilot.graph.state import ResearchState
from damask_copilot.memory.scientific_memory import ScientificMemoryLayer
from damask_copilot.schemas.critic_report import CriticReport
from damask_copilot.tools.postprocessing import postprocess_results


class AnalysisAndCriticAgent:
    """Analyze post-processed outputs, compare with experiment, and choose the next step."""

    name = "analysis_critic"

    def __init__(
        self,
        *,
        use_llm: bool = False,
        model_name: str | None = None,
        llm_runner=None,
        scientific_memory: ScientificMemoryLayer | None = None,
    ) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner
        self.scientific_memory = scientific_memory or ScientificMemoryLayer()

    def run(self, state: ResearchState) -> ResearchState:
        if state.postprocessing_result is None:
            state.postprocessing_result = postprocess_results(state)

        state.alignment_result = self._build_alignment_result(state)
        state.critique = self._build_critique(state)
        state.next_action = self._build_next_action(state)
        state.iteration_decision = self._build_iteration_decision(state)
        state.critic_report = self._build_critic_report(state)
        self.scientific_memory.remember_analysis(state)
        return state.append_trace(
            self.name,
            "analysis_completed",
            {
                "next_action": state.next_action,
                "alignment_status": (state.alignment_result or {}).get("status"),
                "postprocess_status": (state.postprocessing_result or {}).get("status"),
            },
        )

    def _build_alignment_result(self, state: ResearchState) -> dict[str, Any]:
        experimental = state.experimental_data or {}
        postprocess = state.postprocessing_result or {}
        comparison = dict(postprocess.get("comparison") or {})

        if not experimental:
            return {
                "status": "not_applicable",
                "summary": "No experimental dataset was provided, so experiment-simulation alignment was skipped.",
                "compared_observables": [],
                "metrics": {},
                "notes": [],
                "requires_human_review": False,
            }

        if not postprocess.get("ok", False):
            return {
                "status": "comparison_not_possible",
                "summary": "Post-processing did not produce observables suitable for experiment comparison.",
                "compared_observables": [],
                "metrics": {},
                "notes": [postprocess.get("error") or "Stress-strain extraction was unavailable."],
                "requires_human_review": True,
            }

        if not comparison.get("ok", False):
            return {
                "status": "comparison_not_possible",
                "summary": comparison.get("error") or "Simulation and experiment could not be compared on a common observable grid.",
                "compared_observables": [],
                "metrics": {},
                "notes": ["Check experimental curve formatting, units, and observable naming."],
                "requires_human_review": True,
            }

        rmse = float(comparison.get("rmse", 0.0))
        max_abs_error = float(comparison.get("max_abs_error", 0.0))
        return {
            "status": "aligned",
            "summary": self._alignment_summary(rmse),
            "compared_observables": ["stress", "strain"],
            "metrics": {
                "rmse": rmse,
                "max_abs_error": max_abs_error,
                "aligned_points": int(comparison.get("aligned_points", 0)),
            },
            "notes": [
                "DAMASK post-processing was executed through the deterministic postprocessing tool path.",
                "Quantitative agreement should be checked alongside constitutive plausibility.",
            ],
            "requires_human_review": rmse > 40.0,
        }

    def _build_critique(self, state: ResearchState) -> dict[str, Any]:
        run_result = state.run_result or {}
        postprocess = state.postprocessing_result or {}
        alignment = state.alignment_result or {}
        workflow_type = state.workflow_type or "simulation_run"
        metrics = dict(alignment.get("metrics") or {})
        rmse = metrics.get("rmse")
        simulation_spec = state.simulation_spec or {}
        parameter_values = dict(simulation_spec.get("parameter_values") or {})

        key_findings: list[str] = []
        limitations: list[str] = []
        recommendations: list[str] = []

        if run_result.get("status") == "success":
            key_findings.append("DAMASK execution completed and produced result files for downstream interpretation.")
        elif run_result.get("status") == "skipped":
            limitations.append("This was a dry run, so scientific conclusions remain provisional.")
        else:
            limitations.append("Execution did not complete successfully, so scientific interpretation is limited.")

        if postprocess.get("ok", False):
            yield_info = dict(postprocess.get("yield_stress") or {})
            hardening = dict(postprocess.get("hardening_rate") or {})
            if yield_info.get("ok"):
                key_findings.append(
                    f"Estimated yield-stress proxy is {yield_info.get('yield_stress'):.3g} at strain {yield_info.get('strain_at_yield'):.4g}."
                )
            if hardening.get("ok"):
                key_findings.append(f"Average hardening-rate proxy is {hardening.get('hardening_rate'):.3g}.")
        else:
            limitations.append(postprocess.get("error") or "Post-processing results were unavailable.")

        alignment_status = alignment.get("status")
        if alignment_status == "aligned" and rmse is not None:
            key_findings.append(f"Experiment-simulation alignment was available with RMSE {rmse:.3g}.")
            if rmse > 25.0:
                limitations.append("The simulated response still deviates materially from experiment.")
                recommendations.append("Update crystal-plasticity parameters before claiming calibration success.")
            else:
                recommendations.append("Current agreement is promising enough to support reporting or targeted refinement.")
        elif alignment_status == "comparison_not_possible":
            limitations.append("Experiment-simulation alignment could not yet be established.")
            recommendations.append("Harmonize observables, units, and extracted curves before further calibration.")
        elif alignment_status == "not_applicable":
            recommendations.append("No experiment was supplied, so prioritize physical plausibility and numerical robustness.")

        physical_validity, validity_notes = self._assess_physical_validity(state)
        limitations.extend(validity_notes)

        if workflow_type == "calibration" and parameter_values:
            recommendations.append("Preserve parameter history so the next iteration can update the calibration target systematically.")

        objective_update = None
        if workflow_type == "calibration" and rmse is not None:
            objective_update = {
                "target": "rmse",
                "current_value": rmse,
                "step_scale": 0.9 if rmse > 25.0 else 0.98,
                "parameters": parameter_values,
            }

        confidence = self._determine_confidence(state, physical_validity)
        return {
            "summary": self._build_summary(state, alignment_status, rmse),
            "key_findings": key_findings,
            "mismatch_analysis": self._build_mismatch_analysis(alignment),
            "physical_validity": physical_validity,
            "confidence": confidence,
            "limitations": _dedupe_preserve_order(limitations),
            "recommended_actions": _dedupe_preserve_order(recommendations),
            "objective_update": objective_update,
            "postprocess_backend": "damask_postprocess_mcp_via_tool",
        }

    def _build_critic_report(self, state: ResearchState) -> CriticReport:
        critique = state.critique or {}
        findings = list(critique.get("key_findings") or [])
        limitations = list(critique.get("limitations") or [])
        next_steps = list(critique.get("recommended_actions") or [])
        if state.next_action is not None:
            next_steps.append(f"Workflow next action: {state.next_action.get('type', 'stop')}.")
        return CriticReport(
            summary=critique.get("summary") or "Scientific analysis completed.",
            strengths=findings,
            limitations=_dedupe_preserve_order(limitations),
            next_steps=_dedupe_preserve_order(next_steps),
        )

    def _build_iteration_decision(self, state: ResearchState) -> dict[str, Any]:
        next_action = self._build_next_action(state)
        action_type = next_action.get("type", "stop")
        action_map = {
            "stop": "finish",
            "update_parameters": "revise_parameters",
            "run_more_simulations": "revise_simulation_plan",
            "change_model": "revise_modeling_strategy",
            "request_human_review": "request_human_input",
        }
        return {
            "action": action_map.get(action_type, "finish"),
            "rationale": next_action.get("reason", "Scientific analysis completed."),
            "continue_research": action_type != "stop",
            "next_focus": self._next_focus_from_action(action_type),
        }

    def _build_next_action(self, state: ResearchState) -> dict[str, str]:
        run_result = state.run_result or {}
        validation = state.validation_result or {}
        alignment = state.alignment_result or {}
        critique = state.critique or {}
        workflow_type = state.workflow_type or "simulation_run"
        failure_category = run_result.get("failure_category")
        rmse = dict(alignment.get("metrics") or {}).get("rmse")

        if state.mode == "dry_run":
            return {"type": "stop", "reason": "Dry run completed after design and analysis review."}
        if not validation.get("ok", True):
            return {"type": "change_model", "reason": "Validation failed, so the simulation design must be revised."}
        if run_result.get("status") in {"failed", "not_available"}:
            if failure_category in {"input", "model"}:
                return {"type": "change_model", "reason": "Execution failed because the current model or inputs are not viable."}
            return {"type": "run_more_simulations", "reason": "Execution failed for an environmental or transient reason; repair and retry."}
        if alignment.get("status") == "comparison_not_possible":
            return {"type": "request_human_review", "reason": "Experiment alignment is not yet trustworthy enough for autonomous calibration."}
        if workflow_type == "calibration" and rmse is not None and rmse > 25.0:
            return {"type": "update_parameters", "reason": "Calibration mismatch remains large, so parameters should be updated."}
        if critique.get("physical_validity") == "weak":
            return {"type": "change_model", "reason": "The simulated response is not physically convincing enough yet."}
        if state.iteration + 1 >= state.max_iterations:
            return {"type": "stop", "reason": "Reached max_iterations."}
        return {"type": "stop", "reason": "Current evidence is sufficient for this iteration."}

    def _build_summary(self, state: ResearchState, alignment_status: str | None, rmse: float | None) -> str:
        run_status = (state.run_result or {}).get("status", "unknown")
        post_status = (state.postprocessing_result or {}).get("status", "unknown")
        if run_status == "skipped":
            return "Dry-run analysis completed without executing DAMASK."
        if run_status in {"failed", "not_available"}:
            return "Execution did not complete successfully; critique is based on validation and logs."
        if alignment_status == "aligned" and rmse is not None:
            return f"DAMASK execution and post-processing completed, with experiment alignment available at RMSE={rmse:.3g}."
        if alignment_status == "comparison_not_possible":
            return "DAMASK execution completed, but experiment alignment remains unresolved."
        return f"Execution status={run_status}; post-processing status={post_status}."

    def _build_mismatch_analysis(self, alignment: dict[str, Any]) -> dict[str, Any]:
        status = alignment.get("status", "not_available")
        metrics = dict(alignment.get("metrics") or {})
        if status != "aligned":
            return {
                "status": status,
                "primary_issue": alignment.get("summary") or "No quantitative comparison was available.",
                "metrics": metrics,
            }

        rmse = float(metrics.get("rmse", 0.0))
        if rmse <= 10.0:
            severity = "low"
        elif rmse <= 25.0:
            severity = "moderate"
        else:
            severity = "high"
        return {
            "status": status,
            "severity": severity,
            "primary_issue": self._alignment_summary(rmse),
            "metrics": metrics,
        }

    def _assess_physical_validity(self, state: ResearchState) -> tuple[str, list[str]]:
        notes: list[str] = []
        postprocess = state.postprocessing_result or {}
        hardening = dict(postprocess.get("hardening_rate") or {})
        yield_info = dict(postprocess.get("yield_stress") or {})
        simulation_spec = state.simulation_spec or {}
        parameter_values = dict(simulation_spec.get("parameter_values") or {})

        hardening_value = hardening.get("hardening_rate")
        if hardening.get("ok") and isinstance(hardening_value, (int, float)) and hardening_value < 0:
            notes.append("Negative average hardening suggests the constitutive response may be unstable or post-yield softening is dominating unexpectedly.")

        yield_value = yield_info.get("yield_stress")
        if yield_info.get("ok") and isinstance(yield_value, (int, float)) and yield_value <= 0:
            notes.append("Non-positive yield stress is physically implausible for the intended loading scenario.")

        if state.material_system and "ni3al" in state.material_system.lower() and parameter_values:
            n_sl = parameter_values.get("n_sl") or parameter_values.get("n")
            if isinstance(n_sl, (int, float)) and n_sl < 5:
                notes.append("Rate sensitivity exponent is unusually low for Ni3Al crystal-plasticity calibration.")

        if not notes:
            return "preliminary", []
        if len(notes) >= 2:
            return "weak", notes
        return "questionable", notes

    def _determine_confidence(self, state: ResearchState, physical_validity: str) -> str:
        run_status = (state.run_result or {}).get("status")
        alignment_status = (state.alignment_result or {}).get("status")
        if run_status != "success":
            return "low"
        if alignment_status != "aligned":
            return "medium" if physical_validity == "preliminary" else "low"
        if physical_validity in {"weak", "questionable"}:
            return "medium"
        return "high"

    def _alignment_summary(self, rmse: float) -> str:
        if rmse <= 10.0:
            return "Experiment and simulation are in close agreement on the available stress-strain observable."
        if rmse <= 25.0:
            return "Experiment and simulation show moderate mismatch that may be resolvable through parameter refinement."
        return "Experiment and simulation show large mismatch, indicating that parameters or modeling assumptions need revision."

    def _next_focus_from_action(self, action_type: str) -> str | None:
        mapping = {
            "update_parameters": "parameter_calibration",
            "run_more_simulations": "execution_retry",
            "change_model": "modeling_strategy",
            "request_human_review": "data_and_alignment_review",
            "stop": "reporting",
        }
        return mapping.get(action_type)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered
