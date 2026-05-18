"""DAMASK input builder agent."""

from __future__ import annotations

from pathlib import Path

from damask_copilot.agents.base import BaseAgent
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.research_state import ResearchState


class DAMASKInputBuilderAgent(BaseAgent):
    """Populate placeholder paths for generated DAMASK input files."""

    name = "input_builder"

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = workspace_root or Path("workspaces")

    def run(self, state: ResearchState) -> ResearchState:
        if state.simulation_plan is None:
            raise ValueError("Simulation plan must be created before generating file paths.")

        workspace = self.workspace_root / state.simulation_plan.workspace
        results_dir = workspace / "results"

        state.generated_files = GeneratedFiles(
            workspace_dir=str(workspace),
            geometry_path=str(workspace / "geometry.vti"),
            load_path=str(workspace / "load.yaml"),
            material_path=str(workspace / "material.yaml"),
            result_path=str(results_dir / "result.hdf5"),
            report_path=str(workspace / "report.md"),
        )
        state.status = "inputs_declared"
        return self.add_trace(
            state,
            "paths_declared",
            {"workspace_dir": str(workspace)},
        )
