"""Simulation checker agent."""

from __future__ import annotations

from pathlib import Path

from damask_copilot.agents.base import BaseAgent
from damask_copilot.policies.safety_policy import enforce_basic_safety
from damask_copilot.policies.simulation_budget import evaluate_budget
from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.research_state import ResearchState


class SimulationCheckerAgent(BaseAgent):
    """Validate the deterministic plan and generated-file declarations."""

    name = "checker"

    def run(self, state: ResearchState) -> ResearchState:
        if state.simulation_plan is None or state.generated_files is None:
            raise ValueError("Simulation plan and generated files must exist before checking.")

        errors: list[str] = []
        warnings: list[str] = []
        checked_paths: list[str] = []
        missing_files: list[str] = []

        safety_errors = enforce_basic_safety(state.simulation_plan)
        budget_errors = evaluate_budget(state.simulation_plan)
        errors.extend(safety_errors)
        errors.extend(budget_errors)

        for file_path in state.generated_files.required_input_paths():
            checked_paths.append(file_path)
            if not Path(file_path).exists():
                missing_files.append(file_path)

        ok = not errors
        if missing_files:
            if state.dry_run:
                warnings.append("Input files are declared but not materialized in dry-run mode.")
            else:
                errors.append("Required generated input files are missing.")
                ok = False

        state.checker_report = CheckerReport(
            ok=ok,
            errors=errors,
            warnings=warnings,
            missing_files=missing_files,
            checked_paths=checked_paths,
        )
        state.status = "checked"
        return self.add_trace(
            state,
            "checked",
            {"ok": ok, "missing_files": len(missing_files), "errors": len(errors)},
        )
