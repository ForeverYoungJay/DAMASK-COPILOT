from pathlib import Path

from damask_copilot.agents.report_writer import ReportWriterAgent
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState


class FailingLLMRunner:
    def run_structured(self, **kwargs):
        raise RuntimeError("mock llm failure")


def test_report_writer_falls_back_when_llm_summary_fails(tmp_path):
    report_path = tmp_path / "report.md"
    state = ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        dry_run=True,
        use_llm=True,
        goal=ResearchGoal(
            user_query="Study FCC aluminum under uniaxial tension",
            material_system="fcc_al",
            objective="Study response under uniaxial tension",
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
    )

    updated = ReportWriterAgent(use_llm=True, llm_runner=FailingLLMRunner()).run(state)

    text = Path(updated.report_path).read_text(encoding="utf-8")
    assert "DAMASK Copilot Report" in text
    assert "No LLM executive summary was generated." in text
    assert any(event.event == "report_written" for event in updated.traces)
    assert any(event.event == "report_llm_fallback" for event in updated.traces)
