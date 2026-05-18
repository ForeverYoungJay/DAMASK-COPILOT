from pathlib import Path

from damask_copilot.agents.simulation_runner import SimulationRunnerAgent
from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


class FakeRunnerClient:
    def run(self, **kwargs):
        return {
            "ok": True,
            "returncode": 0,
            "stdout_tail": ["done"],
            "stderr_tail": [],
            "executable": "/tmp/DAMASK_grid",
            "result_files": [],
        }

    def collect_results(self, *, workspace: str):
        return {"ok": True, "files": [f"/tmp/{workspace}/result.hdf5"]}


def test_runner_agent_collects_result_files(tmp_path):
    workspace = tmp_path / "fcc_al_smoke_test"
    workspace.mkdir(parents=True, exist_ok=True)
    state = ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        smoke_test=True,
        generated_files=GeneratedFiles(
            workspace_dir=str(workspace),
            geometry_path=str(workspace / "geometry.vti"),
            load_path=str(workspace / "load.yaml"),
            material_path=str(workspace / "material.yaml"),
            research_state_path=str(workspace / "research_state.json"),
            result_path=str(workspace / "results" / "result.hdf5"),
            report_path=str(workspace / "report.md"),
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
        checker_report=CheckerReport(ok=True, status="passed"),
    )

    updated = SimulationRunnerAgent(runner_client=FakeRunnerClient()).run(state)

    assert updated.run_report is not None
    assert updated.run_report.status == "success"
    assert updated.run_report.result_files == ["/tmp/fcc_al_smoke_test/result.hdf5"]
    assert Path(updated.run_report.log_file).exists()
