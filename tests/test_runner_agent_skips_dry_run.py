from damask_copilot.agents.simulation_runner import SimulationRunnerAgent
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


def test_runner_agent_skips_dry_run():
    state = ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        dry_run=True,
        generated_files=GeneratedFiles(
            workspace_dir="workspaces/fcc_al_smoke_test",
            geometry_path="workspaces/fcc_al_smoke_test/geometry.vti",
            load_path="workspaces/fcc_al_smoke_test/load.yaml",
            material_path="workspaces/fcc_al_smoke_test/material.yaml",
            research_state_path="workspaces/fcc_al_smoke_test/research_state.json",
            result_path="workspaces/fcc_al_smoke_test/results/result.hdf5",
            report_path="workspaces/fcc_al_smoke_test/report.md",
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

    updated = SimulationRunnerAgent().run(state)

    assert updated.run_report is not None
    assert updated.run_report.status == "skipped"
    assert updated.run_report.ok is True
