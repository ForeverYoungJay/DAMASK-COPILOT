"""Simulation checker agent."""

from __future__ import annotations

from pathlib import Path

from damask_copilot.agents.base import BaseAgent
from damask_copilot.policies.safety_policy import enforce_basic_safety
from damask_copilot.policies.simulation_budget import evaluate_budget
from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.research_state import ResearchState


class SimulationCheckerAgent(BaseAgent):
    """Validate the plan, material card, and generated dry-run input files."""

    name = "checker"
    max_auto_cells = 16 * 16 * 16
    max_auto_grains = 20

    def run(self, state: ResearchState) -> ResearchState:
        if state.simulation_plan is None or state.generated_files is None or state.material_card is None:
            raise ValueError("Simulation plan, material card, and generated files must exist before checking.")

        errors: list[str] = []
        warnings: list[str] = []
        checked_paths: list[str] = []
        missing_files: list[str] = []
        assumptions: list[str] = list(state.material_card.explicit_assumptions)
        next_steps: list[str] = []

        errors.extend(enforce_basic_safety(state.simulation_plan))
        errors.extend(evaluate_budget(state.simulation_plan))
        errors.extend(self._enforce_auto_limits(state))

        if state.material_card.confidence.lower() == "low" and not assumptions:
            errors.append("Low-confidence material parameters require at least one explicit assumption.")
            next_steps.append("Add an explicit assumption or replace the parameter card with a higher-confidence source.")

        if state.material_card.is_demo_template:
            warnings.append("Material parameters come from a demo/template card and should not be treated as validated.")
            next_steps.append("Replace demo/template parameters before running production simulations.")

        if "stress_strain_curve" not in state.simulation_plan.outputs:
            warnings.append("Simulation plan does not request stress_strain_curve output.")
            next_steps.append("Include stress_strain_curve in the requested outputs.")

        for file_path in state.generated_files.required_input_paths():
            checked_paths.append(file_path)
            if not Path(file_path).exists():
                missing_files.append(file_path)

        if missing_files:
            errors.append("Required generated input files are missing.")

        ok = not errors
        state.checker_report = CheckerReport(
            ok=ok,
            errors=errors,
            warnings=warnings,
            missing_files=missing_files,
            checked_paths=checked_paths,
            assumptions=assumptions,
            next_steps=next_steps,
        )
        state.status = "checked"
        return self.add_trace(
            state,
            "checked",
            {"ok": ok, "missing_files": len(missing_files), "errors": len(errors)},
        )

    def _enforce_auto_limits(self, state: ResearchState) -> list[str]:
        total_cells = 1
        for cell in state.simulation_plan.geometry.cells:
            total_cells *= cell

        errors: list[str] = []
        if total_cells > self.max_auto_cells:
            errors.append(f"Planned cell count {total_cells} exceeds automatic dry-run limit {self.max_auto_cells}.")
        if state.simulation_plan.geometry.grains > self.max_auto_grains:
            errors.append(
                f"Planned grain count {state.simulation_plan.geometry.grains} exceeds automatic limit {self.max_auto_grains}."
            )
        return errors
