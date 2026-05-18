import json
from pathlib import Path

from damask_copilot.agents.damask_input_builder import DAMASKInputBuilderAgent
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


def test_input_builder_generates_files(monkeypatch, tmp_path):
    def fake_create_material_yaml(path, *args, **kwargs):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("material", encoding="utf-8")
        return {"ok": True, "path": path}

    def fake_create_simple_tension_load_yaml(path, *args, **kwargs):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("load", encoding="utf-8")
        return {"ok": True, "path": path}

    def fake_create_voronoi_grid(path, *args, **kwargs):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("geometry", encoding="utf-8")
        return {"ok": True, "path": path}

    monkeypatch.setattr(
        "damask_copilot.agents.damask_input_builder.create_material_yaml",
        fake_create_material_yaml,
    )
    monkeypatch.setattr(
        "damask_copilot.agents.damask_input_builder.create_simple_tension_load_yaml",
        fake_create_simple_tension_load_yaml,
    )
    monkeypatch.setattr(
        "damask_copilot.agents.damask_input_builder.create_voronoi_grid",
        fake_create_voronoi_grid,
    )

    state = ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        material_card=MaterialParameterCard(
            material_id="fcc_al",
            material_name="FCC Aluminum Demo",
            crystal_structure="fcc",
            phase_type="phenopowerlaw",
            source_path="data/materials/fcc_al_demo.yaml",
            confidence="medium",
            explicit_assumptions=["Demo parameters are acceptable for smoke-test planning only."],
            is_demo_template=True,
            parameters={"elastic": {"type": "Hooke"}, "plastic": {"type": "phenopowerlaw"}},
        ),
        simulation_plan=SimulationPlan(
            name="fcc_al_smoke_test",
            summary="Small tension smoke test.",
            workspace="fcc_al_smoke_test",
            material_id="fcc_al",
            outputs=["stress_strain_curve"],
            geometry=GeometrySpec(grid_type="voronoi", cells=[8, 8, 8], size=[1.0, 1.0, 1.0], grains=8),
            loading=LoadingSpec(mode="uniaxial_tension", direction="x", final_strain=0.02, strain_rate=1.0e-3, steps=5),
        ),
    )

    updated = DAMASKInputBuilderAgent(workspace_root=tmp_path).run(state)

    assert updated.generated_files is not None
    assert Path(updated.generated_files.material_path).exists()
    assert Path(updated.generated_files.load_path).exists()
    assert Path(updated.generated_files.geometry_path).exists()
    assert Path(updated.generated_files.research_state_path).exists()
    payload = json.loads(Path(updated.generated_files.research_state_path).read_text(encoding="utf-8"))
    assert payload["simulation_plan"]["name"] == "fcc_al_smoke_test"
