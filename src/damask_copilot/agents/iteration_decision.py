"""Generic iteration decision agent for the materials research graph."""

from __future__ import annotations

from damask_copilot.graph.materials_research_state import MaterialsResearchState, append_trace
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import IterationDecisionOutput


class IterationDecisionAgent:
    """Choose the next route for an iterative materials research cycle."""

    name = "iteration_decision"

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
            prompt_name="iteration_decider",
            system_prompt=load_prompt("iteration_decider"),
            user_prompt=(
                f"User query: {state.get('user_query')}\n"
                f"Iteration: {state.get('iteration', 0)} / {state.get('max_iterations', 1)}\n"
                f"Experimental data summary: {state.get('experimental_data_summary')}\n"
                f"Project plan: {state.get('project_plan')}\n"
                f"Checker report: {state.get('checker_report')}\n"
                f"Alignment report: {state.get('alignment_report')}\n"
                f"Critic report: {state.get('critic_report')}\n"
                f"Parameter card: {state.get('parameter_card')}"
            ),
            output_schema=IterationDecisionOutput,
            model_name=state.get("model") or self.model_name,
        )
        action = parsed.action or ("finish" if not parsed.continue_research else "revise_simulation_plan")
        updated = dict(state)
        updated["iteration_decision"] = {
            "action": action,
            "rationale": parsed.rationale,
            "continue_research": parsed.continue_research,
            "next_focus": parsed.next_focus,
        }
        return append_trace(updated, self.name, "iteration_decided_llm", {"action": action, "rationale": parsed.rationale})

    def _run_deterministic(self, state: MaterialsResearchState) -> MaterialsResearchState:
        action = "finish"
        rationale = "Current pass is sufficient for reporting."

        checker = state.get("checker_report")
        project_plan = state.get("project_plan")
        if checker is not None and getattr(checker, "status", None) == "blocked":
            action = "revise_simulation_plan"
            rationale = "The simulation checker vetoed the current setup."
        elif dict(state.get("experimental_data_summary") or {}).get("needs_human_correction"):
            action = "request_human_input"
            rationale = "Critical experimental metadata is missing."
        elif project_plan is None:
            action = "revise_project_plan"
            rationale = "A project-level roadmap is required before another simulation plan is proposed."
        elif dict(state.get("alignment_report") or {}).get("status") == "comparison_not_possible":
            action = "revise_experimental_data"
            rationale = "Experiment-simulation alignment could not be established."
        else:
            parameter_card = state.get("parameter_card")
            if isinstance(parameter_card, dict):
                review_flags = list(parameter_card.get("parameters", {}).get("review_flags", []))
            else:
                review_flags = list(getattr(parameter_card, "parameters", {}).get("review_flags", [])) if parameter_card is not None else []
            if review_flags and state.get("mode") != "dry_run":
                action = "revise_parameters"
                rationale = "Low-confidence or template parameters remain unresolved."
            elif state.get("iteration", 0) + 1 < state.get("max_iterations", 1) and state.get("mode") == "dry_run":
                action = "finish"
                rationale = "Dry-run completed; further iterations should be triggered explicitly."

        updated = dict(state)
        updated["iteration_decision"] = {
            "action": action,
            "rationale": rationale,
            "continue_research": action != "finish",
        }
        return append_trace(updated, self.name, "iteration_decided", {"action": action, "rationale": rationale})
