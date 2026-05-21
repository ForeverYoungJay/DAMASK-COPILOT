from pathlib import Path

from damask_copilot.graph.state import ResearchState
from damask_copilot.graph.workflow import damask_copilot_workflow


def test_workflow_persists_agent_execution_records(tmp_path, monkeypatch):
    monkeypatch.setenv("DAMASK_COPILOT_LITERATURE_AUTO_SEARCH", "0")
    workspace = tmp_path / "workflow_records"
    state = ResearchState(
        user_goal="Run a dry-run DAMASK workflow for Ni3Al",
        mode="dry_run",
        max_iterations=1,
        literature_files=[],
        literature_sources=[],
        experimental_files=[],
        user_files=[],
        workspace=str(workspace),
    )

    final_state = damask_copilot_workflow(state)

    records_dir = Path(final_state.workspace) / "agent_records"
    assert records_dir.exists()
    assert (records_dir / "index.json").exists()

    record_files = sorted(path.name for path in records_dir.glob("*.json") if path.name != "index.json")
    assert any("research_manager" in name for name in record_files)
    assert any("scientific_knowledge" in name for name in record_files)
    assert any("project_planner" in name for name in record_files)
    assert any("simulation_designer" in name for name in record_files)
    assert any("damask_validation" in name for name in record_files)
    assert any("damask_execution" in name for name in record_files)
    assert any("analysis_critic" in name for name in record_files)
    assert any("research_report" in name for name in record_files)
