import json
from pathlib import Path

import yaml

from damask_copilot.agents.damask_input_builder import DAMASKInputBuilderAgent
from damask_copilot.mcp_clients.damask_preprocess_client import DAMASKPreprocessClient
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


class FakePreprocessClient(DAMASKPreprocessClient):
    def create_material_yaml(self, *, path: str, **kwargs) -> dict:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("orientation: [1.0, 0.0, 0.0, 0.0]\n", encoding="utf-8")
        return {"ok": True, "path": path, "material_count": 1}

    def create_material_yaml_from_template(self, *, path: str, homogenization: dict, phase: dict, material: list[dict]) -> dict:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            yaml.safe_dump(
                {
                    "homogenization": homogenization,
                    "phase": phase,
                    "material": material,
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return {"ok": True, "path": path, "material_count": len(material)}

    def create_simple_tension_load_yaml(self, *, path: str, **kwargs) -> dict:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("load", encoding="utf-8")
        return {"ok": True, "path": path}

    def create_voronoi_grid(self, *, path: str, **kwargs) -> dict:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("geometry", encoding="utf-8")
        return {"ok": True, "path": path, "material_count": kwargs.get("grains", 1)}

    def inspect_grid(self, *, path: str) -> dict:
        return {"ok": True, "path": path, "material_count": 8}

    def inspect_material_yaml(self, *, path: str) -> dict:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return {"ok": True, "path": path, "material_count": len(payload.get("material", []))}

    def add_material_entry(
        self,
        *,
        path: str,
        homogenization: str,
        phase: str,
        orientation_quaternion: list[float],
        volume_fraction: float = 1.0,
    ) -> dict:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        materials = list(payload.get("material", []))
        materials.append(
            {
                "homogenization": homogenization,
                "constituents": [{"phase": phase, "O": orientation_quaternion, "v": volume_fraction}],
            }
        )
        payload["material"] = materials
        Path(path).write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
        return {"ok": True, "path": path, "material_count": len(materials)}

    def create_random_orientations(self, *, count: int, seed: int = 0) -> list[list[float]]:
        return [[1.0, 0.0, 0.0, float(index)] for index in range(count)]


def _state(tmp_path: Path, *, overwrite: bool) -> ResearchState:
    return ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        dry_run=True,
        overwrite=overwrite,
        goal=ResearchGoal(
            user_query="Study FCC aluminum under uniaxial tension",
            material_system="fcc_al",
            objective="Study response under uniaxial tension",
        ),
        material_card=MaterialParameterCard(
            material_id="fcc_al",
            material_name="FCC Aluminum Demo",
            crystal_structure="fcc",
            phase_type="phenopowerlaw",
            source_path="data/materials/fcc_al_demo.yaml",
            confidence="medium",
            explicit_assumptions=["Demo parameters are acceptable for smoke-test planning only."],
            is_demo_template=True,
            parameters={
                "elastic": {"C_11": 1.0, "C_12": 1.0, "C_44": 1.0},
                "plastic": {"type": "phenopowerlaw"},
                "damask": {
                    "materialpoint": {
                        "homogenization": {"SX": {"N_constituents": 1, "mechanical": {"type": "pass"}}},
                        "phase": {"Aluminum": {"lattice": "cF", "mechanical": {"elastic": {"type": "Hooke"}}}},
                    },
                    "numerics": {"solver": {"grid": {"N_staggered_iter_max": 10}}},
                },
            },
        ),
        simulation_plan=SimulationPlan(
            name=tmp_path.name,
            summary="Small tension smoke test.",
            workspace=tmp_path.name,
            material_id="fcc_al",
            outputs=["stress_strain_curve"],
            geometry=GeometrySpec(grid_type="voronoi", cells=[8, 8, 8], size=[1.0, 1.0, 1.0], grains=8),
            loading=LoadingSpec(mode="uniaxial_tension", direction="x", final_strain=0.02, strain_rate=1.0e-3, steps=5),
        ),
    )


def test_input_builder_generates_files_and_serializes_generated_paths(tmp_path):
    workspace_root = tmp_path / "workspaces"
    state = _state(workspace_root / "fcc_al_smoke_test", overwrite=True)

    updated = DAMASKInputBuilderAgent(
        workspace_root=workspace_root,
        preprocess_client=FakePreprocessClient(),
    ).run(state)

    assert updated.generated_files is not None
    assert Path(updated.generated_files.material_path).exists()
    assert Path(updated.generated_files.load_path).exists()
    assert Path(updated.generated_files.geometry_path).exists()
    assert Path(updated.generated_files.numerics_path).exists()
    snapshot = json.loads(Path(updated.generated_files.research_state_path).read_text(encoding="utf-8"))
    assert snapshot["generated_files"]["material_path"] == updated.generated_files.material_path
    assert snapshot["generated_files"]["report_path"] == updated.generated_files.report_path
    assert snapshot["generated_files"]["numerics_path"] == updated.generated_files.numerics_path
    material_text = Path(updated.generated_files.material_path).read_text(encoding="utf-8")
    numerics_text = Path(updated.generated_files.numerics_path).read_text(encoding="utf-8")
    assert "homogenization:" in material_text
    assert "phase:" in material_text
    assert "material:" in material_text
    assert material_text.count("phase: Aluminum") == 8
    assert "solver:" in numerics_text
    assert "grid:" in numerics_text


def test_input_builder_overwrite_cleans_stale_workspace(tmp_path):
    workspace_root = tmp_path / "workspaces"
    workspace = workspace_root / "fcc_al_smoke_test"
    workspace.mkdir(parents=True, exist_ok=True)
    stale_file = workspace / "stress_strain.csv"
    stale_file.write_text("stale", encoding="utf-8")

    state = _state(workspace, overwrite=True)
    updated = DAMASKInputBuilderAgent(
        workspace_root=workspace_root,
        preprocess_client=FakePreprocessClient(),
    ).run(state)

    assert updated.generated_files is not None
    assert not stale_file.exists()
    assert Path(updated.generated_files.material_path).exists()
