"""Simulation planner agent."""

from __future__ import annotations

from damask_copilot.agents.base import BaseAgent
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import SimulationPlannerOutput
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


class SimulationPlannerAgent(BaseAgent):
    """Create a deterministic smoke-test plan."""

    name = "simulation_planner"

    def __init__(self, *, use_llm: bool = False, model_name: str | None = None, llm_runner: StructuredLLMRunner | None = None) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state: ResearchState) -> ResearchState:
        if self.use_llm or state.use_llm:
            return self._run_llm(state)
        return self._run_deterministic(state)

    def _run_llm(self, state: ResearchState) -> ResearchState:
        if state.goal is None:
            raise ValueError("Research goal must be set before planning a simulation.")

        material_slug = state.selected_material_key or state.goal.material_system
        runner = self.llm_runner or StructuredLLMRunner(model_name=state.model_name or self.model_name)
        parsed = runner.run_structured(
            prompt_name="simulation_planner",
            system_prompt=load_prompt("simulation_planner"),
            user_prompt=(
                f"User query: {state.user_query}\n"
                f"Material system: {state.goal.material_system}\n"
                f"Objective: {state.goal.objective}\n"
                f"Selected material key: {material_slug}\n"
                f"Material notes: {state.notes}\n"
                f"Smoke test requested: {state.smoke_test}"
            ),
            output_schema=SimulationPlannerOutput,
            model_name=state.model_name or self.model_name,
        )
        state.simulation_planner_output = parsed
        plan_name = parsed.plan_name
        state.simulation_plan = SimulationPlan(
            name=plan_name,
            summary=parsed.summary,
            workspace=plan_name,
            material_id=material_slug,
            outputs=parsed.outputs or ["stress_strain_curve"],
            geometry=GeometrySpec(
                grid_type=parsed.grid_type,
                cells=self._normalize_cells(parsed.cells),
                size=self._normalize_size(parsed.size),
                grains=min(20, max(1, parsed.grains)),
            ),
            loading=LoadingSpec(
                mode=parsed.loading_mode,
                direction=parsed.loading_direction,
                final_strain=min(0.05, max(1.0e-6, parsed.final_strain)),
                strain_rate=parsed.strain_rate,
                steps=min(50, max(1, parsed.steps)),
            ),
        )
        state.status = "plan_created"
        return self.add_trace(state, "plan_created_llm", self.model_dump(parsed))

    def _run_deterministic(self, state: ResearchState) -> ResearchState:
        if state.goal is None:
            raise ValueError("Research goal must be set before planning a simulation.")

        loading_mode = "uniaxial_tension"
        if "compression" in state.goal.objective.lower():
            loading_mode = "uniaxial_compression"

        material_slug = state.selected_material_key or state.goal.material_system
        plan_name = f"{material_slug}_smoke_test"

        state.simulation_plan = SimulationPlan(
            name=plan_name,
            summary=f"Small deterministic {loading_mode} smoke test for {material_slug}.",
            workspace=plan_name,
            material_id=material_slug,
            outputs=["stress_strain_curve"],
            geometry=GeometrySpec(
                grid_type="voronoi",
                cells=[8, 8, 8],
                size=[1.0, 1.0, 1.0],
                grains=8,
            ),
            loading=LoadingSpec(
                mode=loading_mode,
                direction="x",
                final_strain=0.02,
                strain_rate=1.0e-3,
                steps=5,
            ),
        )
        state.status = "plan_created"
        return self.add_trace(
            state,
            "plan_created",
            {"workspace": plan_name, "mode": loading_mode},
        )

    @staticmethod
    def _normalize_cells(cells: list[int]) -> list[int]:
        normalized = [min(16, max(1, int(value))) for value in cells[:3]]
        while len(normalized) < 3:
            normalized.append(8)
        return normalized

    @staticmethod
    def _normalize_size(size: list[float]) -> list[float]:
        normalized = [max(1.0e-9, float(value)) for value in size[:3]]
        while len(normalized) < 3:
            normalized.append(1.0)
        return normalized
