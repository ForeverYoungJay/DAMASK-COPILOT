from pathlib import Path

from damask_copilot.agents.simulation_checker import SimulationCheckerAgent
from damask_copilot.mcp_clients.damask_preprocess_client import DAMASKPreprocessClient
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


class FakePreprocessInspector(DAMASKPreprocessClient):
    def __init__(self, *, grid_count: int, material_count: int) -> None:
        self.grid_count = grid_count
        self.material_count = material_count

    def inspect_grid(self, *, path: str) -> dict:
        return {"ok": True, "path": path, "material_count": self.grid_count}

    def inspect_material_yaml(self, *, path: str) -> dict:
        return {"ok": True, "path": path, "material_count": self.material_count}


def _state(tmp_path: Path) -> ResearchState:
    geometry_path = tmp_path / "geometry.vti"
    load_path = tmp_path / "load.yaml"
    material_path = tmp_path / "material.yaml"
    research_state_path = tmp_path / "research_state.json"
    for path in [geometry_path, load_path, material_path, research_state_path]:
        path.write_text("x", encoding="utf-8")
    return ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        generated_files=GeneratedFiles(
            workspace_dir=str(tmp_path),
            geometry_path=str(geometry_path),
            load_path=str(load_path),
            material_path=str(material_path),
            research_state_path=str(research_state_path),
            result_path=str(tmp_path / "results" / "result.hdf5"),
            report_path=str(tmp_path / "report.md"),
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
            parameters={},
        ),
        simulation_plan=SimulationPlan(
            name="fcc_al_smoke_test",
            summary="Small smoke test.",
            workspace="fcc_al_smoke_test",
            material_id="fcc_al",
            outputs=["stress_strain_curve"],
            geometry=GeometrySpec(grid_type="voronoi", cells=[8, 8, 8], size=[1.0, 1.0, 1.0], grains=8),
            loading=LoadingSpec(mode="uniaxial_tension", direction="x", final_strain=0.02, strain_rate=1.0e-3, steps=5),
        ),
    )


def test_checker_blocks_on_geometry_material_count_mismatch(tmp_path):
    state = _state(tmp_path)
    updated = SimulationCheckerAgent(
        preprocess_client=FakePreprocessInspector(grid_count=8, material_count=1)
    ).run(state)

    assert updated.checker_report is not None
    assert updated.checker_report.ok is False
    assert updated.checker_report.status == "blocked"
    assert any("Geometry/material mismatch" in item for item in updated.checker_report.errors)


def test_checker_passes_when_geometry_material_count_matches(tmp_path):
    state = _state(tmp_path)
    updated = SimulationCheckerAgent(
        preprocess_client=FakePreprocessInspector(grid_count=8, material_count=8)
    ).run(state)

    assert updated.checker_report is not None
    assert updated.checker_report.ok is True
