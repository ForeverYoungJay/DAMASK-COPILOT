"""Hypothesis generation agent."""

from __future__ import annotations

from damask_copilot.graph.materials_research_state import MaterialsResearchState, append_trace
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import HypothesisAgentOutput


class HypothesisAgent:
    """Generate testable hypotheses from the current research framing."""

    name = "hypothesis_agent"

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
            prompt_name="hypothesis_agent",
            system_prompt=load_prompt("hypothesis_agent"),
            user_prompt=(
                f"User query: {state.get('user_query')}\n"
                f"Research case: {state.get('research_case')}\n"
                f"Literature review: {state.get('literature_review')}\n"
                f"Experimental data summary: {state.get('experimental_data_summary')}\n"
                f"Modeling strategy: {state.get('modeling_strategy')}\n"
                f"Material knowledge: {state.get('material_knowledge')}"
            ),
            output_schema=HypothesisAgentOutput,
            model_name=state.get("model") or self.model_name,
        )
        hypotheses = [item.model_dump() for item in parsed.hypotheses]
        if not hypotheses:
            return self._run_deterministic(state)
        updated = dict(state)
        updated["hypotheses"] = hypotheses
        return append_trace(updated, self.name, "hypotheses_defined_llm", {"count": len(hypotheses)})

    def _run_deterministic(self, state: MaterialsResearchState) -> MaterialsResearchState:
        research_case = dict(state.get("research_case") or {})
        literature_review = dict(state.get("literature_review") or {})
        experimental_data = dict(state.get("experimental_data_summary") or {})
        mechanism_notes = list(dict(state.get("material_knowledge") or {}).get("mechanisms", []))
        observables = list(experimental_data.get("observable_candidates", []))
        loading_mode = research_case.get("loading_mode", "mechanical_loading")
        representation = dict(state.get("modeling_strategy") or {}).get("simulation_abstraction", "DAMASK smoke test")

        evidence: list[str] = []
        if literature_review.get("mechanisms"):
            evidence.extend([f"Literature mechanism: {item}" for item in literature_review.get("mechanisms", [])[:2]])
        if literature_review.get("planning_implications"):
            evidence.extend([f"Literature planning hint: {item}" for item in literature_review.get("planning_implications", [])[:2]])
        if observables:
            evidence.append(f"Experimental observables available: {', '.join(observables)}")
        if not evidence:
            evidence.append("Unsupported by external evidence in the current state; treated as a planning hypothesis.")

        hypotheses = [
            {
                "id": "H1",
                "statement": f"The dominant response under {loading_mode} can be explored with a {representation} DAMASK configuration.",
                "evidence": list(evidence),
                "required_simulation": representation,
                "expected_observable": observables[0] if observables else "stress_strain_curve",
                "risks": [
                    "The selected abstraction may omit deformation modes outside the current loading proxy.",
                    "Parameter confidence may be insufficient for quantitative claims.",
                ],
            }
        ]
        if mechanism_notes:
            hypotheses.append(
                {
                    "id": "H2",
                    "statement": f"Mechanisms such as {mechanism_notes[0]} should influence the simulated observables.",
                    "evidence": [f"Material knowledge note: {mechanism_notes[0]}"],
                    "required_simulation": representation,
                    "expected_observable": observables[0] if observables else "texture_or_stress_response",
                    "risks": ["Current inputs may not include enough state variables to isolate this mechanism."],
                }
            )

        updated = dict(state)
        updated["hypotheses"] = hypotheses
        return append_trace(updated, self.name, "hypotheses_defined", {"count": len(hypotheses)})
