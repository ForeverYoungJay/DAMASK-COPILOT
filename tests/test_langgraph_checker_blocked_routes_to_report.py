from pathlib import Path

from damask_copilot.graph.runner import run_research_graph
from damask_copilot.schemas.checker_report import CheckerReport


class _BlockedCheckerAgent:
    def run(self, state):
        state.checker_report = CheckerReport(ok=False, status="blocked", errors=["Unsafe configuration."])
        state.traces.append({"agent": "checker", "event": "blocked", "details": {}})
        return state


def test_langgraph_checker_blocked_routes_to_report(monkeypatch):
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
        "damask_copilot.agents.damask_input_builder.create_material_yaml",
        fake_create_material_yaml,
    )
    monkeypatch.setattr(
        "damask_copilot.agents.damask_input_builder.create_simple_tension_load_yaml",
        fake_create_simple_tension_load_yaml,
    )
    monkeypatch.setattr(
        "damask_copilot.agents.damask_input_builder.create_voronoi_grid",
        fake_create_voronoi_grid,
    )

    final_state = run_research_graph(
        user_query="Study FCC aluminum under uniaxial tension",
        mode="dry_run",
        use_llm=False,
        model=None,
        max_iterations=1,
        allow_overwrite=True,
        checkpoint=False,
        agent_overrides={"simulation_checker": _BlockedCheckerAgent()},
        stream=False,
    )

    assert final_state["checker_report"].status == "blocked"
    assert final_state["report_path"] is not None
    assert Path(final_state["report_path"]).exists()
    assert not any(item["agent"] == "approval_gate" for item in final_state["trace"])
    assert final_state["run_report"] is None
