from damask_copilot.agents.scientific_critic import ScientificCriticAgent
from damask_copilot.schemas.critic_report import CriticReport
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.postprocess_report import PostprocessReport
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.run_report import RunReport


def test_scientific_critic_smoke_test_adds_preliminary_and_recommendations():
    state = ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        material_card=MaterialParameterCard(
            material_id="fcc_al",
            material_name="FCC Aluminum Demo",
            crystal_structure="fcc",
            phase_type="phenopowerlaw",
            source_path="data/materials/fcc_al_demo.yaml",
            confidence="medium",
            explicit_assumptions=[],
            is_demo_template=True,
            parameters={},
        ),
        run_report=RunReport(ok=True, status="success"),
        postprocess_report=PostprocessReport(
            ok=True,
            status="success",
            result_file="result.hdf5",
            inspected_fields=["F", "P"],
            stress_strain_csv="stress_strain.csv",
            vtk_dir="vtk",
            summary="done",
        ),
    )

    updated = ScientificCriticAgent(use_llm=False).run(state)

    assert updated.critic_report is not None
    assert "Preliminary" in updated.critic_report.summary
    assert any("physical claim" in item for item in updated.critic_report.limitations)
    assert any("Demo/template" in item for item in updated.critic_report.limitations)
    assert "Verify material.yaml with literature parameters." in updated.critic_report.next_steps
