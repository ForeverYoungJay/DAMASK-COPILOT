from pathlib import Path

from damask_copilot.agents.report_writer import ReportWriterAgent
from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


def test_report_writer_writes_expected_sections(tmp_path):
    report_path = tmp_path / "report.md"
    state = ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        dry_run=True,
        use_llm=False,
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
            parameters={},
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
        generated_files=GeneratedFiles(
            workspace_dir=str(tmp_path),
            geometry_path=str(tmp_path / "geometry.vti"),
            load_path=str(tmp_path / "load.yaml"),
            material_path=str(tmp_path / "material.yaml"),
            research_state_path=str(tmp_path / "research_state.json"),
            result_path=str(tmp_path / "results" / "result.hdf5"),
            report_path=str(report_path),
        ),
        checker_report=CheckerReport(
            ok=True,
            warnings=["Material parameters come from a demo/template card and should not be treated as validated."],
            assumptions=["Demo parameters are acceptable for smoke-test planning only."],
            next_steps=["Replace demo/template parameters before running production simulations."],
        ),
    )

    updated = ReportWriterAgent().run(state)

    text = Path(updated.report_path).read_text(encoding="utf-8")
    assert "## Research Goal" in text
    assert "## Material Card" in text
    assert "## Simulation Plan" in text
    assert "## Generated Files" in text
    assert "## Checker Report" in text
    assert "## Assumptions" in text
    assert "## Next Recommended Simulations" in text
    assert "report_writer: report_written" in text
