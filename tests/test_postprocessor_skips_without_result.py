from damask_copilot.agents.postprocessor import PostProcessingAgent
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.research_state import ResearchState


def test_postprocessor_skips_without_result():
    state = ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        generated_files=GeneratedFiles(
            workspace_dir="workspaces/fcc_al_smoke_test",
            geometry_path="workspaces/fcc_al_smoke_test/geometry.vti",
            load_path="workspaces/fcc_al_smoke_test/load.yaml",
            material_path="workspaces/fcc_al_smoke_test/material.yaml",
            research_state_path="workspaces/fcc_al_smoke_test/research_state.json",
            result_path="workspaces/fcc_al_smoke_test/results/result.hdf5",
            report_path="workspaces/fcc_al_smoke_test/report.md",
        ),
    )

    updated = PostProcessingAgent().run(state)

    assert updated.postprocess_report is not None
    assert updated.postprocess_report.status == "skipped"
    assert updated.postprocess_report.ok is True
