"""Iteration decider agent."""

from __future__ import annotations

from damask_copilot.graph.state import DamaskResearchState, append_trace
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import IterationDecisionOutput


class IterationDeciderAgent:
    """Decide whether to continue another research iteration."""

    name = "iteration_decider"

    def __init__(self, *, use_llm: bool = False, model_name: str | None = None, llm_runner: StructuredLLMRunner | None = None) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state: DamaskResearchState) -> DamaskResearchState:
        if self.use_llm or state.get("use_llm", False):
            return self._run_llm(state)
        return self._run_deterministic(state)

    def _run_llm(self, state: DamaskResearchState) -> DamaskResearchState:
        runner = self.llm_runner or StructuredLLMRunner(model_name=state.get("model") or self.model_name)
        parsed = runner.run_structured(
            prompt_name="iteration_decider",
            system_prompt=load_prompt("iteration_decider"),
            user_prompt=(
                f"User query: {state['user_query']}\n"
                f"Mode: {state.get('mode')}\n"
                f"Iteration: {state.get('iteration', 0)} / {state.get('max_iterations', 1)}\n"
                f"Checker report: {state.get('checker_report')}\n"
                f"Run report: {state.get('run_report')}\n"
                f"Postprocess report: {state.get('postprocess_report')}\n"
                f"Critic report: {state.get('critic_report')}"
            ),
            output_schema=IterationDecisionOutput,
            model_name=state.get("model") or self.model_name,
        )
        updated = dict(state)
        updated["iteration_decision"] = parsed
        return append_trace(updated, self.name, "iteration_decided_llm", {
            "continue_research": parsed.continue_research,
            "rationale": parsed.rationale,
            "next_focus": parsed.next_focus,
        })

    def _run_deterministic(self, state: DamaskResearchState) -> DamaskResearchState:
        continue_research = False
        rationale = "Stop after the current pass unless a higher-level controller requests another iteration."
        if state.get("checker_report") is not None and getattr(state["checker_report"], "ok", False) is False:
            rationale = "Stop because checker vetoed the current setup."
        updated = dict(state)
        updated["iteration_decision"] = IterationDecisionOutput(
            continue_research=continue_research,
            rationale=rationale,
            next_focus=None,
        )
        return append_trace(updated, self.name, "iteration_decided", {
            "continue_research": continue_research,
            "rationale": rationale,
        })
