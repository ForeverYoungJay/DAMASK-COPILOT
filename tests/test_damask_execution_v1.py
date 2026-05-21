from pathlib import Path

from damask_copilot.agents.damask_execution import DAMASKExecutionAgent
from damask_copilot.graph.state import ResearchState


def test_damask_execution_v1_skips_dry_run(tmp_path):
    state = ResearchState(
        user_goal="Run Ni3Al DAMASK simulation.",
        mode="dry_run",
        workspace=str(tmp_path / "workspace"),
        needs_damask_simulation=True,
    )

    updated = DAMASKExecutionAgent().run(state)

    assert updated.run_result is not None
    assert updated.run_result["status"] == "skipped"
    assert updated.run_result["failure_category"] is None


def test_damask_execution_v1_collects_results_after_success(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    geometry_path = workspace / "geometry.vti"
    load_path = workspace / "load.yaml"
    material_path = workspace / "material.yaml"
    for path in [geometry_path, load_path, material_path]:
        path.write_text("stub", encoding="utf-8")

    monkeypatch.setattr(
        "damask_copilot.agents.damask_execution.run_damask_grid",
        lambda **kwargs: {
            "ok": True,
            "status": "success",
            "log_path": str(workspace / "run.log"),
            "result_files": [],
            "failure_category": None,
        },
    )
    monkeypatch.setattr(
        "damask_copilot.agents.damask_execution.collect_result_files",
        lambda workdir: {
            "ok": True,
            "count": 1,
            "result_files": [str(workspace / "results" / "result.hdf5")],
        },
    )
    monkeypatch.setattr(
        "damask_copilot.agents.damask_execution.parse_damask_log",
        lambda log_path: {"ok": True, "log_path": log_path, "detected_errors": {"matched_errors": [], "has_errors": False}},
    )

    state = ResearchState(
        user_goal="Run Ni3Al DAMASK simulation.",
        mode="smoke_test",
        workspace=str(workspace),
        geometry_path=str(geometry_path),
        load_yaml_path=str(load_path),
        material_yaml_path=str(material_path),
        needs_damask_simulation=True,
    )

    updated = DAMASKExecutionAgent().run(state)

    assert updated.run_result["status"] == "success"
    assert updated.run_result["result_files"] == [str(workspace / "results" / "result.hdf5")]
    assert updated.run_result["execution_decision"]["action"] == "postprocess"


def test_damask_execution_v1_reports_environment_failure(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    geometry_path = workspace / "geometry.vti"
    load_path = workspace / "load.yaml"
    material_path = workspace / "material.yaml"
    for path in [geometry_path, load_path, material_path]:
        path.write_text("stub", encoding="utf-8")

    monkeypatch.setattr(
        "damask_copilot.agents.damask_execution.run_damask_grid",
        lambda **kwargs: {
            "ok": False,
            "status": "not_available",
            "log_path": str(workspace / "run.log"),
            "result_files": [],
            "error": "DAMASK_grid executable not found.",
            "failure_category": "environment",
        },
    )
    monkeypatch.setattr(
        "damask_copilot.agents.damask_execution.parse_damask_log",
        lambda log_path: {"ok": True, "log_path": log_path, "detected_errors": {"matched_errors": ["missing_file_or_executable"], "has_errors": True}},
    )

    state = ResearchState(
        user_goal="Run Ni3Al DAMASK simulation.",
        mode="smoke_test",
        workspace=str(workspace),
        geometry_path=str(geometry_path),
        load_yaml_path=str(load_path),
        material_yaml_path=str(material_path),
        needs_damask_simulation=True,
    )

    updated = DAMASKExecutionAgent().run(state)

    assert updated.run_result["status"] == "not_available"
    assert updated.run_result["failure_category"] == "environment"
    assert updated.run_result["execution_decision"]["action"] == "repair_or_stub"
