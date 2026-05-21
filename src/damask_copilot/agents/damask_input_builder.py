"""Deprecated DAMASK input-builder micro-agent retained for compatibility wrappers."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

from damask_copilot.agents._deprecation import warn_legacy_agent
from damask_copilot.agents.base import BaseAgent
from damask_copilot.mcp_clients.damask_preprocess_client import DAMASKPreprocessClient
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.research_state import ResearchState


class DAMASKInputBuilderAgent(BaseAgent):
    """Deprecated wrapper for input generation.

    The unified v1 architecture uses `SimulationDesignerAgent` plus
    deterministic tools in `damask_copilot.tools`.
    """

    name = "input_builder"

    def __init__(self, workspace_root: Path | None = None, preprocess_client: DAMASKPreprocessClient | None = None) -> None:
        warn_legacy_agent(legacy_name="DAMASKInputBuilderAgent", replacement="SimulationDesignerAgent")
        self.workspace_root = workspace_root or Path("workspaces")
        self.preprocess_client = preprocess_client or DAMASKPreprocessClient()

    def run(self, state: ResearchState) -> ResearchState:
        if state.simulation_plan is None or state.material_card is None:
            raise ValueError("Simulation plan and material card must be created before generating input files.")

        workspace = self.workspace_root / state.simulation_plan.name
        if workspace.exists() and any(workspace.iterdir()) and not state.overwrite:
            raise FileExistsError(
                f"Workspace already exists and is not empty: {workspace}. Use --overwrite to replace generated inputs."
            )
        if workspace.exists() and state.overwrite:
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        results_dir = workspace / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        material_path = workspace / "material.yaml"
        load_path = workspace / "load.yaml"
        numerics_path = workspace / "numerics.yaml"
        geometry_path = workspace / "geometry.vti"
        research_state_path = workspace / "research_state.json"
        report_path = workspace / "report.md"

        state.generated_files = GeneratedFiles(
            workspace_dir=str(workspace),
            geometry_path=str(geometry_path),
            load_path=str(load_path),
            material_path=str(material_path),
            numerics_path=str(numerics_path),
            research_state_path=str(research_state_path),
            result_path=str(results_dir / "result.hdf5"),
            report_path=str(report_path),
        )

        self._generate_geometry(state, geometry_path)
        self._generate_material(state, material_path, geometry_path)
        self._generate_load(state, load_path)
        self._generate_numerics(state, numerics_path)
        self._write_research_state(state, research_state_path)
        state.status = "inputs_generated"
        return self.add_trace(
            state,
            "inputs_generated",
            {
                "workspace_dir": str(workspace),
                "material_path": str(material_path),
                "load_path": str(load_path),
                "numerics_path": str(numerics_path),
                "geometry_path": str(geometry_path),
                "research_state_path": str(research_state_path),
            },
        )

    def _generate_material(self, state: ResearchState, material_path: Path, geometry_path: Path) -> None:
        card = state.material_card
        parameters = card.parameters
        damask_materialpoint = dict(parameters.get("damask", {}).get("materialpoint", {}))
        homogenization = dict(damask_materialpoint.get("homogenization", {}))
        phase = dict(damask_materialpoint.get("phase", {}))
        if not homogenization or not phase:
            elastic = dict(parameters.get("elastic", {}))
            plastic = dict(parameters.get("plastic", {})) or None
            lattice = str(parameters.get("damask_lattice", parameters.get("crystal_structure", card.crystal_structure)))
            homogenization_label = state.simulation_plan.material_id
            phase_label = card.material_id
            self.preprocess_client.create_material_yaml(
                path=str(material_path),
                material_name=homogenization_label,
                phase_name=phase_label,
                lattice=lattice,
                elastic=elastic,
                plastic=plastic,
            )
        else:
            homogenization_label = next(iter(homogenization))
            phase_label = next(iter(phase))
            base_material = [
                {
                    "homogenization": homogenization_label,
                    "constituents": [{"phase": phase_label, "O": [1.0, 0.0, 0.0, 0.0], "v": 1.0}],
                }
            ]
            self.preprocess_client.create_material_yaml_from_template(
                path=str(material_path),
                homogenization=homogenization,
                phase=phase,
                material=base_material,
            )

        grid_info = self.preprocess_client.inspect_grid(path=str(geometry_path))
        if not grid_info.get("ok", False):
            raise ValueError(f"Failed to inspect generated geometry for material mapping: {grid_info.get('error', 'unknown error')}")

        material_count = int(grid_info.get("material_count", 1))
        if material_count <= 1:
            return

        orientations = self.preprocess_client.create_random_orientations(count=material_count, seed=0)
        for orientation in orientations[1:material_count]:
            self.preprocess_client.add_material_entry(
                path=str(material_path),
                homogenization=homogenization_label,
                phase=phase_label,
                orientation_quaternion=[float(value) for value in orientation],
                volume_fraction=1.0,
            )

    def _generate_load(self, state: ResearchState, load_path: Path) -> None:
        loading = state.simulation_plan.loading
        if "compression" in loading.mode.lower():
            self.preprocess_client.create_simple_compression_load_yaml(
                path=str(load_path),
                strain_rate=loading.strain_rate,
                final_strain=loading.final_strain,
                steps=loading.steps,
            )
            return
        self.preprocess_client.create_simple_tension_load_yaml(
            path=str(load_path),
            strain_rate=loading.strain_rate,
            final_strain=loading.final_strain,
            steps=loading.steps,
        )

    def _generate_geometry(self, state: ResearchState, geometry_path: Path) -> None:
        geometry = state.simulation_plan.geometry
        self.preprocess_client.create_voronoi_grid(
            path=str(geometry_path),
            cells=geometry.cells,
            size=geometry.size,
            grains=geometry.grains,
            seed=0,
        )

    def _generate_numerics(self, state: ResearchState, numerics_path: Path) -> None:
        numerics = dict(state.material_card.parameters.get("damask", {}).get("numerics", {}))
        if not numerics:
            numerics = {
                "solver": {
                    "grid": {
                        "N_staggered_iter_max": 10,
                        "eps_abs_div_P": 1.0e-10,
                        "eps_rel_div_P": 1.0e-4,
                        "eps_abs_P": 1.0e3,
                        "eps_rel_P": 5.0e-4,
                    }
                }
            }
        numerics_path.write_text(yaml.safe_dump(numerics, sort_keys=False), encoding="utf-8")

    def _write_research_state(self, state: ResearchState, research_state_path: Path) -> None:
        serializer = getattr(state, "model_dump", None)
        payload = serializer() if serializer is not None else state.dict()
        research_state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
