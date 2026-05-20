from pathlib import Path

from langgraph.types import Command

from damask_copilot.agents.damask_input_builder import DAMASKInputBuilderAgent
from damask_copilot.graph.materials_research_graph import build_materials_research_graph
from damask_copilot.graph.materials_research_state import create_initial_materials_state


def test_materials_graph_interrupts_at_human_review_and_can_resume(monkeypatch, tmp_path):
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

    app = build_materials_research_graph(
        checkpoint=True,
        use_llm=False,
        agent_overrides={"damask_input_builder": DAMASKInputBuilderAgent(workspace_root=tmp_path / "workspaces")},
    )
    config = {"configurable": {"thread_id": "materials-interrupt-resume-test"}}
    initial = create_initial_materials_state(
        user_query="Study FCC aluminum under uniaxial tension",
        mode="dry_run",
        use_llm=False,
        max_iterations=1,
        user_constraints={"allow_overwrite": True},
    )

    first = app.invoke(initial, config=config)
    assert "__interrupt__" in first
    snapshot = app.get_state(config)
    assert snapshot.next == ("human_review_framing",)
    assert snapshot.interrupts

    resumed = app.invoke(
        Command(
            resume={
                "decision": "approve",
                "comments": "Proceed with framing.",
                "state_patch": {
                    "user_constraints": {
                        "allow_overwrite": True,
                        "auto_human_feedback": {"decision": "approve", "comments": "Auto-approve later review points."},
                    }
                },
            }
        ),
        config=config,
    )

    assert resumed.get("report_path") is not None
    assert resumed.get("human_feedback_history")
    assert app.get_state(config).next == ()


def test_materials_graph_run_and_resume_persisted_checkpoint(monkeypatch, tmp_path):
    from damask_copilot.graph.materials_research_graph import (
        resume_materials_research_graph,
        run_materials_research_graph,
    )

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

    checkpoint_path = tmp_path / "materials-checkpoints.pkl"
    thread_id = "materials-persisted-resume-test"

    first = run_materials_research_graph(
        "Study FCC aluminum under uniaxial tension",
        mode="dry_run",
        use_llm=False,
        max_iterations=1,
        checkpoint=True,
        checkpoint_path=checkpoint_path,
        thread_id=thread_id,
        agent_overrides={"damask_input_builder": DAMASKInputBuilderAgent(workspace_root=tmp_path / "workspaces")},
        stream=False,
    )

    assert "__interrupt__" in first
    assert checkpoint_path.exists()

    resumed = resume_materials_research_graph(
        thread_id=thread_id,
        decision="approve",
        comments="Proceed.",
        state_patch={
            "user_constraints": {
                "allow_overwrite": True,
                "auto_human_feedback": {"decision": "approve", "comments": "Auto-approve later reviews."},
            }
        },
        checkpoint=True,
        checkpoint_path=checkpoint_path,
        agent_overrides={"damask_input_builder": DAMASKInputBuilderAgent(workspace_root=tmp_path / "workspaces")},
        stream=False,
    )

    assert resumed.get("report_path") is not None
    assert resumed.get("__thread_id__") == thread_id
