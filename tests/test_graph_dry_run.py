from pathlib import Path

from damask_copilot.graph.simple_runner import run_research_graph
from damask_copilot.schemas.research_state import ResearchState


def test_graph_dry_run_writes_report_and_skips_execution():
    state = ResearchState(
        user_query="Study FCC Al under uniaxial tension",
        dry_run=True,
    )

    final_state = run_research_graph(state)

    assert final_state.goal is not None
    assert final_state.material_card is not None
    assert final_state.simulation_plan is not None
    assert final_state.generated_files is not None
    assert final_state.checker_report is not None
    assert final_state.checker_report.ok is True
    assert final_state.run_report is None
    assert final_state.report_path is not None
    assert Path(final_state.report_path).exists()
    assert "DAMASK Copilot Report" in Path(final_state.report_path).read_text(encoding="utf-8")
