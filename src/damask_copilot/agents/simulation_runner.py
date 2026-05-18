"""Simulation runner agent."""

from __future__ import annotations

from pathlib import Path

from damask_copilot.agents.base import BaseAgent
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.run_report import RunReport


class SimulationRunnerAgent(BaseAgent):
    """Run or skip the DAMASK simulation."""

    name = "runner"

    def run(self, state: ResearchState) -> ResearchState:
        if state.generated_files is None:
            raise ValueError("Generated file paths must be defined before the runner executes.")

        if state.dry_run:
            state.run_report = RunReport(
                ok=True,
                skipped=True,
                dry_run=True,
                result_file=state.generated_files.result_path,
                message="Simulation execution skipped because dry_run=True.",
            )
            state.status = "run_skipped"
            return self.add_trace(state, "skipped", {"reason": "dry_run"})

        result_file = Path(state.generated_files.result_path)
        if result_file.exists():
            state.run_report = RunReport(
                ok=True,
                skipped=False,
                dry_run=False,
                result_file=str(result_file),
                message="Existing result file detected.",
            )
        else:
            state.run_report = RunReport(
                ok=False,
                skipped=True,
                dry_run=False,
                result_file=str(result_file),
                message="Runner is a placeholder and did not execute DAMASK yet.",
            )
        state.status = "run_finished"
        return self.add_trace(state, "runner_completed", {"ok": state.run_report.ok})
