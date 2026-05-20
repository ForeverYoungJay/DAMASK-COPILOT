"""Modeling strategy selection agent."""

from __future__ import annotations

from damask_copilot.graph.materials_research_state import MaterialsResearchState, append_trace
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import ModelingStrategyOutput


class ModelingStrategyAgent:
    """Choose a DAMASK modeling abstraction appropriate for the case."""

    name = "modeling_strategy_agent"

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
            prompt_name="modeling_strategy_agent",
            system_prompt=load_prompt("modeling_strategy_agent"),
            user_prompt=(
                f"User query: {state.get('user_query')}\n"
                f"Research case: {state.get('research_case')}\n"
                f"Literature review: {state.get('literature_review')}\n"
                f"Experimental data summary: {state.get('experimental_data_summary')}\n"
                f"Hypotheses: {state.get('hypotheses')}"
            ),
            output_schema=ModelingStrategyOutput,
            model_name=state.get("model") or self.model_name,
        )
        strategy = parsed.model_dump()
        if "stress_strain_curve" not in strategy["required_outputs"]:
            strategy["required_outputs"] = sorted(set(strategy["required_outputs"] + ["stress_strain_curve"]))
        updated = dict(state)
        updated["modeling_strategy"] = strategy
        return append_trace(updated, self.name, "modeling_strategy_defined_llm", {
            "simulation_abstraction": strategy["simulation_abstraction"],
            "requires_human_review": strategy["requires_human_review"],
        })

    def _run_deterministic(self, state: MaterialsResearchState) -> MaterialsResearchState:
        research_case = dict(state.get("research_case") or {})
        experimental_data = dict(state.get("experimental_data_summary") or {})
        literature_review = dict(state.get("literature_review") or {})
        loading_mode = research_case.get("loading_mode", "uniaxial_tension")
        microstructure = research_case.get("microstructure", "polycrystal")

        if microstructure == "single_crystal":
            abstraction = "single_crystal"
            grains = 1
            geometry = "single_orientation_rve"
        else:
            abstraction = "polycrystal_rve"
            grains = 8 if state.get("mode") != "full_run" else 32
            geometry = "voronoi_rve"

        comparison_targets = []
        if experimental_data.get("observable_candidates"):
            comparison_targets = [f"match_{item}" for item in experimental_data["observable_candidates"]]
        elif literature_review.get("observables_for_validation"):
            comparison_targets = list(literature_review["observables_for_validation"])
        elif "stress_strain_curve" not in comparison_targets:
            comparison_targets = ["stress_strain_curve"]

        assumptions = [
            f"Use a {geometry} representation as a proxy for the requested case.",
            "The current strategy is intended for screening unless validated parameters and metadata are available.",
        ]
        for item in literature_review.get("planning_implications", [])[:2]:
            if item not in assumptions:
                assumptions.append(item)
        limitations = [
            "This abstraction may not capture all boundary conditions implied by the real experiment.",
            "Rolling, cyclic, and shear paths may require richer load histories than the current deterministic builder supports.",
        ]
        requires_human_review = bool(
            experimental_data.get("critical_metadata_missing")
            or research_case.get("requires_complex_loading", False)
            or state.get("mode") == "full_run"
        )

        strategy = {
            "simulation_abstraction": abstraction,
            "geometry_strategy": geometry,
            "loading_proxy": loading_mode,
            "target_grains": grains,
            "comparison_targets": comparison_targets,
            "required_outputs": sorted(set(["stress_strain_curve"] + comparison_targets)),
            "assumptions": assumptions,
            "limitations": limitations,
            "requires_human_review": requires_human_review,
        }
        updated = dict(state)
        updated["modeling_strategy"] = strategy
        return append_trace(updated, self.name, "modeling_strategy_defined", {
            "simulation_abstraction": abstraction,
            "requires_human_review": requires_human_review,
        })
