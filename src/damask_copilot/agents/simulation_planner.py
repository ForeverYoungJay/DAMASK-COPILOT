"""Deprecated simulation-planner micro-agent retained for compatibility wrappers."""

from __future__ import annotations

import re

from damask_copilot.agents.base import BaseAgent
from damask_copilot.agents._deprecation import warn_legacy_agent
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import SimulationPlannerOutput
from damask_copilot.schemas.project_plan import CandidateSimulation
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


class SimulationPlannerAgent(BaseAgent):
    """Deprecated wrapper for simulation planning.

    The unified v1 architecture uses `SimulationDesignerAgent` instead.
    """

    name = "simulation_planner"

    def __init__(self, *, use_llm: bool = False, model_name: str | None = None, llm_runner: StructuredLLMRunner | None = None) -> None:
        warn_legacy_agent(legacy_name="SimulationPlannerAgent", replacement="SimulationDesignerAgent")
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

        candidate = self._resolve_candidate_simulation(state)
        material_slug = state.selected_material_key or (state.material_card.material_id if state.material_card else None) or state.goal.material_system
        runner = self.llm_runner or StructuredLLMRunner(model_name=state.model_name or self.model_name)
        parsed = runner.run_structured(
            prompt_name="simulation_planner",
            system_prompt=load_prompt("simulation_planner"),
            user_prompt=(
                f"User query: {state.user_query}\n"
                f"Material system: {state.goal.material_system}\n"
                f"Objective: {state.goal.objective}\n"
                f"Selected material key: {material_slug}\n"
                f"Project plan: {self._jsonable(state.project_plan)}\n"
                f"Target simulation id: {state.selected_simulation_id}\n"
                f"Selected candidate simulation: {self._jsonable(candidate)}\n"
                f"Material notes: {state.notes}\n"
                f"Smoke test requested: {state.smoke_test}"
            ),
            output_schema=SimulationPlannerOutput,
            model_name=state.model_name or self.model_name,
        )
        state.simulation_planner_output = parsed
        target_simulation_id = state.selected_simulation_id or (candidate.simulation_id if candidate is not None else None)
        plan_name = self._normalize_plan_name(parsed.plan_name, material_slug, target_simulation_id)
        summary = parsed.summary
        if target_simulation_id:
            summary = f"[{target_simulation_id}] {summary}"
        state.simulation_plan = SimulationPlan(
            name=plan_name,
            summary=summary,
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
        return self.add_trace(
            state,
            "plan_created_llm",
            {
                **self.model_dump(parsed),
                "target_simulation_id": target_simulation_id,
            },
        )

    def _run_deterministic(self, state: ResearchState) -> ResearchState:
        if state.goal is None:
            raise ValueError("Research goal must be set before planning a simulation.")

        candidate = self._resolve_candidate_simulation(state)
        loading_mode = self._determine_loading_mode(state, candidate)
        material_slug = state.selected_material_key or (state.material_card.material_id if state.material_card else None) or state.goal.material_system
        target_simulation_id = state.selected_simulation_id or (candidate.simulation_id if candidate is not None else "smoke_test")
        plan_name = self._normalize_plan_name(f"{material_slug}_{target_simulation_id}", material_slug, target_simulation_id)
        grains = 8
        if state.project_plan is not None and state.candidate_simulations:
            grains = 12 if state.smoke_test else 16
        if candidate is not None and (candidate.simulation_type_hint or "").lower().startswith("single_crystal"):
            grains = 1
        summary = f"Executable {loading_mode} DAMASK plan for {material_slug}."
        if candidate is not None:
            summary = f"Executable {loading_mode} DAMASK plan for {candidate.simulation_id}: {candidate.objective}"

        state.simulation_plan = SimulationPlan(
            name=plan_name,
            summary=summary,
            workspace=plan_name,
            material_id=material_slug,
            outputs=["stress_strain_curve"],
            geometry=GeometrySpec(
                grid_type="voronoi",
                cells=[8, 8, 8],
                size=[1.0, 1.0, 1.0],
                grains=grains,
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
            {
                "workspace": plan_name,
                "mode": loading_mode,
                "target_simulation_id": target_simulation_id,
            },
        )

    @staticmethod
    def _jsonable(value):
        if value is None:
            return None
        dumper = getattr(value, "model_dump", None)
        if dumper is not None:
            return dumper()
        if hasattr(value, "dict"):
            return value.dict()
        return value

    @staticmethod
    def _normalize_plan_name(plan_name: str, material_slug: str, target_simulation_id: str | None) -> str:
        if target_simulation_id and target_simulation_id.lower().replace("-", "_") not in plan_name.lower():
            base = f"{material_slug}_{target_simulation_id}"
        else:
            base = plan_name
        return re.sub(r"[^a-zA-Z0-9_]+", "_", base).strip("_").lower()

    @staticmethod
    def _resolve_candidate_simulation(state: ResearchState) -> CandidateSimulation | None:
        selected = state.selected_simulation_id
        for item in state.candidate_simulations:
            if item.simulation_id == selected:
                return item
        if selected:
            raise ValueError(f"Selected simulation id '{selected}' was not found in candidate_simulations.")
        return state.candidate_simulations[0] if state.candidate_simulations else None

    @staticmethod
    def _determine_loading_mode(state: ResearchState, candidate: CandidateSimulation | None) -> str:
        loading_mode = "uniaxial_tension"
        candidate_hint = (candidate.simulation_type_hint if candidate is not None else None) or ""
        lowered = f"{state.goal.objective} {candidate_hint}".lower()
        if "rolling" in lowered:
            return "plane_strain_rolling_proxy"
        if "compression" in lowered:
            return "uniaxial_compression"
        if "shear" in lowered:
            return "simple_shear"
        return loading_mode

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
