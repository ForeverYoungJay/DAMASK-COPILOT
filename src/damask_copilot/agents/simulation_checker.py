"""Deprecated simulation-checker micro-agent retained for compatibility wrappers."""

from __future__ import annotations

from pathlib import Path

from damask_copilot.agents._deprecation import warn_legacy_agent
from damask_copilot.agents.base import BaseAgent
from damask_copilot.mcp_clients.damask_preprocess_client import DAMASKPreprocessClient
from damask_copilot.policies.safety_policy import enforce_basic_safety
from damask_copilot.policies.simulation_budget import evaluate_budget
from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.research_state import ResearchState


class SimulationCheckerAgent(BaseAgent):
    """Deprecated wrapper for deterministic validation.

    The unified v1 architecture uses `damask_copilot.tools.validation`.
    """

    name = "checker"
    max_auto_cells = 16 * 16 * 16
    max_auto_grains = 20

    def __init__(self, preprocess_client: DAMASKPreprocessClient | None = None) -> None:
        warn_legacy_agent(legacy_name="SimulationCheckerAgent", replacement="damask_copilot.tools.validation")
        self.preprocess_client = preprocess_client or DAMASKPreprocessClient()

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
        else:
            errors.extend(self._check_material_mapping_consistency(state))

        ok = not errors
        state.checker_report = CheckerReport(
            ok=ok,
            status="passed" if ok else "blocked",
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

    def _check_material_mapping_consistency(self, state: ResearchState) -> list[str]:
        grid_info = self.preprocess_client.inspect_grid(path=state.generated_files.geometry_path)
        if not grid_info.get("ok", False):
            return [f"Failed to inspect geometry.vti: {grid_info.get('error', 'unknown error')}"]

        material_info = self.preprocess_client.inspect_material_yaml(path=state.generated_files.material_path)
        if not material_info.get("ok", False):
            return [f"Failed to inspect material.yaml: {material_info.get('error', 'unknown error')}"]

        geometry_material_count = int(grid_info.get("material_count", 0))
        material_yaml_count = int(material_info.get("material_count", 0))
        if geometry_material_count != material_yaml_count:
            return [
                "Geometry/material mismatch: geometry.vti material_count "
                f"({geometry_material_count}) does not match material.yaml material entries ({material_yaml_count})."
            ]
        return []
