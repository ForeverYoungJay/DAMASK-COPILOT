from pathlib import Path

from damask_copilot.graph.runner import run_research_graph
from damask_copilot.schemas.postprocess_report import PostprocessReport
from damask_copilot.schemas.run_report import RunReport


class _RunnerSuccessAgent:
    def run(self, state):
        workspace = Path(state.generated_files.workspace_dir)
        result_file = workspace / "result.hdf5"
        result_file.write_text("result", encoding="utf-8")
        state.run_report = RunReport(
            ok=True,
            status="success",
            command="DAMASK_grid --geom geometry.vti --load load.yaml --material material.yaml",
            returncode=0,
            result_files=[str(result_file)],
        )
        state.traces.append({"agent": "runner", "event": "runner_completed", "details": {}})
        return state


class _PostprocessorSuccessAgent:
    def run(self, state):
        workspace = Path(state.generated_files.workspace_dir)
        csv_path = workspace / "stress_strain.csv"
        csv_path.write_text("strain,stress\n0.0,0.0\n", encoding="utf-8")
        state.postprocess_report = PostprocessReport(
            ok=True,
            status="success",
            result_file=state.run_report.result_files[0],
            inspected_fields=["F", "P"],
            stress_strain_csv=str(csv_path),
            vtk_dir=None,
            summary="Mock post-processing completed.",
            warnings=[],
        )
        state.traces.append({"agent": "postprocessor", "event": "postprocessed", "details": {}})
        return state


def test_langgraph_smoke_test_routes_to_runner(monkeypatch):
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
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.create_material_yaml",
        lambda self, *, path, **kwargs: fake_create_material_yaml(path),
    )
    monkeypatch.setattr(
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.create_material_yaml_from_template",
        lambda self, *, path, **kwargs: fake_create_material_yaml(path),
    )
    monkeypatch.setattr(
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.create_simple_tension_load_yaml",
        lambda self, *, path, **kwargs: fake_create_simple_tension_load_yaml(path),
    )
    monkeypatch.setattr(
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.create_voronoi_grid",
        lambda self, *, path, **kwargs: fake_create_voronoi_grid(path),
    )
    monkeypatch.setattr(
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.inspect_grid",
        lambda self, *, path: {"ok": True, "path": path, "material_count": 8},
    )
    monkeypatch.setattr(
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.inspect_material_yaml",
        lambda self, *, path: {"ok": True, "path": path, "material_count": 8},
    )
    monkeypatch.setattr(
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.add_material_entry",
        lambda self, **kwargs: {"ok": True, "path": kwargs["path"], "material_count": 8},
    )
    monkeypatch.setattr(
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.create_random_orientations",
        lambda self, *, count, seed=0: [[1.0, 0.0, 0.0, float(i)] for i in range(count)],
    )

    final_state = run_research_graph(
        user_query="Study FCC aluminum under uniaxial tension",
        mode="smoke_test",
        use_llm=False,
        model=None,
        max_iterations=1,
        allow_overwrite=True,
        checkpoint=False,
        agent_overrides={
            "simulation_runner": _RunnerSuccessAgent(),
            "postprocessor": _PostprocessorSuccessAgent(),
        },
        stream=False,
    )

    assert final_state["approval_status"] == "approved"
    assert final_state["run_report"].status == "success"
    assert final_state["postprocess_report"].status == "success"
    assert any(item["agent"] == "runner" for item in final_state["trace"])
