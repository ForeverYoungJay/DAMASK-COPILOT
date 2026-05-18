"""Simulation runner agent."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from damask_copilot.agents.base import BaseAgent
from damask_copilot.mcp_clients.damask_runner_client import DAMASKRunnerClient
from damask_copilot.policies.simulation_budget import MAX_TOTAL_CELLS
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.run_report import RunReport


class SimulationRunnerAgent(BaseAgent):
    """Run or skip the DAMASK simulation."""

    name = "runner"

    def __init__(self, runner_client: DAMASKRunnerClient | None = None) -> None:
        self.runner_client = runner_client or DAMASKRunnerClient()

    def run(self, state: ResearchState) -> ResearchState:
        if state.generated_files is None or state.simulation_plan is None:
            raise ValueError("Generated file paths and simulation plan must be defined before the runner executes.")

        if state.dry_run:
            state.run_report = RunReport(
                ok=True,
                status="skipped",
                message="Simulation execution skipped because dry_run=True.",
            )
            state.status = "run_skipped"
            return self.add_trace(state, "skipped", {"reason": "dry_run"})

        if state.checker_report and state.checker_report.status == "blocked":
            state.run_report = RunReport(
                ok=False,
                status="skipped",
                message="Simulation execution blocked by checker_report.status == blocked.",
            )
            state.status = "run_blocked"
            return self.add_trace(state, "skipped", {"reason": "checker_blocked"})

        if not state.smoke_test and not state.allow_full_run:
            state.run_report = RunReport(
                ok=False,
                status="skipped",
                message="Full DAMASK execution requires explicit --full-run approval.",
            )
            state.status = "run_blocked"
            return self.add_trace(state, "skipped", {"reason": "full_run_not_allowed"})

        total_cells = 1
        for cell in state.simulation_plan.geometry.cells:
            total_cells *= cell
        if total_cells > MAX_TOTAL_CELLS:
            state.run_report = RunReport(
                ok=False,
                status="failed",
                message=f"Planned cell count {total_cells} exceeds execution budget {MAX_TOTAL_CELLS}.",
            )
            state.status = "run_blocked"
            return self.add_trace(state, "runner_blocked", {"reason": "budget_exceeded", "cells": total_cells})

        started_at = datetime.now(UTC).isoformat()
        workspace_name = state.simulation_plan.name
        run_result = self.runner_client.run(
            workspace=workspace_name,
            geometry="geometry.vti",
            load="load.yaml",
            material="material.yaml",
            numerics="numerics.yaml" if state.generated_files.numerics_path else None,
            timeout_seconds=3600,
        )
        finished_at = datetime.now(UTC).isoformat()
        log_path = Path(state.generated_files.workspace_dir) / "run.log"
        stdout_tail = list(run_result.get("stdout_tail", []))
        stderr_tail = list(run_result.get("stderr_tail", []))
        log_text = "\n".join(
            [
                "[stdout_tail]",
                *stdout_tail,
                "",
                "[stderr_tail]",
                *stderr_tail,
            ]
        )
        log_path.write_text(log_text + "\n", encoding="utf-8")
        result_files = run_result.get("result_files", [])
        if not result_files:
            collected = self.runner_client.collect_results(workspace=workspace_name)
            result_files = collected.get("files", [])
        command = self._build_command(run_result, include_numerics=bool(state.generated_files.numerics_path))
        state.run_report = RunReport(
            ok=bool(run_result.get("ok", False)),
            status="success" if run_result.get("ok", False) else "failed",
            command=command,
            returncode=run_result.get("returncode"),
            stdout_tail=stdout_tail,
            stderr_tail=stderr_tail,
            log_file=str(log_path),
            result_files=result_files,
            started_at=started_at,
            finished_at=finished_at,
            message=run_result.get("error") or ("DAMASK_grid completed." if run_result.get("ok", False) else "DAMASK_grid failed."),
        )
        state.status = "run_finished"
        return self.add_trace(
            state,
            "runner_completed",
            {"ok": state.run_report.ok, "status": state.run_report.status, "result_count": len(state.run_report.result_files)},
        )

    @staticmethod
    def _build_command(run_result: dict, *, include_numerics: bool) -> str | None:
        executable = run_result.get("executable")
        if not executable:
            return None
        numerics_segment = " --numerics numerics.yaml" if include_numerics else ""
        return f"{executable} --geom geometry.vti --load load.yaml --material material.yaml{numerics_segment} --workingdir <workspace>"
