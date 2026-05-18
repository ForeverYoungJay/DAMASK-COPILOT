"""Research manager agent."""

from __future__ import annotations

from damask_copilot.agents.base import BaseAgent
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import ResearchManagerOutput
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState


class ResearchManagerAgent(BaseAgent):
    """Infer a coarse research goal from the user query."""

    name = "research_manager"

    def __init__(self, *, use_llm: bool = False, model_name: str | None = None, llm_runner: StructuredLLMRunner | None = None) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state: ResearchState) -> ResearchState:
        if self.use_llm or state.use_llm:
            return self._run_llm(state)
        return self._run_deterministic(state)

    def _run_llm(self, state: ResearchState) -> ResearchState:
        runner = self.llm_runner or StructuredLLMRunner(model_name=state.model_name or self.model_name)
        parsed = runner.run_structured(
            prompt_name="research_manager",
            system_prompt=load_prompt("research_manager"),
            user_prompt=f"User query: {state.user_query}",
            output_schema=ResearchManagerOutput,
            model_name=state.model_name or self.model_name,
        )
        state.research_manager_output = parsed
        state.goal = ResearchGoal(
            user_query=state.user_query,
            material_system=parsed.material_system,
            objective=parsed.objective,
        )
        state.status = "goal_defined"
        return self.add_trace(state, "goal_inferred_llm", self.model_dump(parsed))

    def _run_deterministic(self, state: ResearchState) -> ResearchState:
        query = state.user_query.strip()
        lowered = query.lower()

        material_system = "generic_material"
        if "fcc al" in lowered or "aluminum" in lowered or " aluminium" in lowered or lowered.startswith("al "):
            material_system = "fcc_al"
        elif "fcc cu" in lowered or "copper" in lowered:
            material_system = "fcc_cu"

        if "compression" in lowered:
            objective = "Study response under uniaxial compression"
        elif "tension" in lowered:
            objective = "Study response under uniaxial tension"
        else:
            objective = "Run an initial smoke-test simulation study"

        state.goal = ResearchGoal(
            user_query=query,
            material_system=material_system,
            objective=objective,
        )
        state.status = "goal_defined"
        return self.add_trace(
            state,
            "goal_inferred",
            {"material_system": material_system, "objective": objective},
        )
