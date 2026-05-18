"""DAMASK input builder agent."""

from __future__ import annotations

import json
from pathlib import Path

from damask_copilot.agents.base import BaseAgent
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.research_state import ResearchState
from damask_mcp_adapter.modules.config_material import create_material_yaml
from damask_mcp_adapter.modules.grid_tools import create_voronoi_grid
from damask_mcp_adapter.modules.loading import create_simple_compression_load_yaml, create_simple_tension_load_yaml


class DAMASKInputBuilderAgent(BaseAgent):
    """Generate DAMASK dry-run input files through the local adapter layer."""

    name = "input_builder"

    def __init__(self, workspace_root: Path | None = None) -> None:
        self.workspace_root = workspace_root or Path("workspaces")

    def run(self, state: ResearchState) -> ResearchState:
        if state.simulation_plan is None or state.material_card is None:
            raise ValueError("Simulation plan and material card must be created before generating input files.")

        workspace = self.workspace_root / state.simulation_plan.name
        if workspace.exists() and any(workspace.iterdir()) and not state.overwrite:
            raise FileExistsError(
                f"Workspace already exists and is not empty: {workspace}. Use --overwrite to replace generated inputs."
            )
        workspace.mkdir(parents=True, exist_ok=True)
        results_dir = workspace / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        material_path = workspace / "material.yaml"
        load_path = workspace / "load.yaml"
        geometry_path = workspace / "geometry.vti"
        research_state_path = workspace / "research_state.json"
        report_path = workspace / "report.md"

        self._generate_material(state, material_path)
        self._generate_load(state, load_path)
        self._generate_geometry(state, geometry_path)
        self._write_research_state(state, research_state_path)

        state.generated_files = GeneratedFiles(
            workspace_dir=str(workspace),
            geometry_path=str(geometry_path),
            load_path=str(load_path),
            material_path=str(material_path),
            research_state_path=str(research_state_path),
            result_path=str(results_dir / "result.hdf5"),
            report_path=str(report_path),
        )
        state.status = "inputs_generated"
        return self.add_trace(
            state,
            "inputs_generated",
            {
                "workspace_dir": str(workspace),
                "material_path": str(material_path),
                "load_path": str(load_path),
                "geometry_path": str(geometry_path),
                "research_state_path": str(research_state_path),
            },
        )

    def _generate_material(self, state: ResearchState, material_path: Path) -> None:
        card = state.material_card
        parameters = card.parameters
        elastic = dict(parameters.get("elastic", {}))
        plastic = dict(parameters.get("plastic", {})) or None
        lattice = str(parameters.get("crystal_structure", card.crystal_structure))
        phase_name = card.material_id
        create_material_yaml(
            str(material_path),
            state.simulation_plan.material_id,
            phase_name,
            lattice,
            elastic,
            plastic,
        )

    def _generate_load(self, state: ResearchState, load_path: Path) -> None:
        loading = state.simulation_plan.loading
        if "compression" in loading.mode.lower():
            create_simple_compression_load_yaml(
                str(load_path),
                loading.strain_rate,
                loading.final_strain,
                loading.steps,
            )
            return
        create_simple_tension_load_yaml(
            str(load_path),
            loading.strain_rate,
            loading.final_strain,
            loading.steps,
        )

    def _generate_geometry(self, state: ResearchState, geometry_path: Path) -> None:
        geometry = state.simulation_plan.geometry
        create_voronoi_grid(
            str(geometry_path),
            geometry.cells,
            geometry.size,
            geometry.grains,
            seed=0,
        )

    def _write_research_state(self, state: ResearchState, research_state_path: Path) -> None:
        serializer = getattr(state, "model_dump", None)
        payload = serializer() if serializer is not None else state.dict()
        research_state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
