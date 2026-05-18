from pathlib import Path

from damask_copilot.graph.runner import run_research_graph
from damask_copilot.graph.state import append_trace
from damask_copilot.schemas.llm_outputs import IterationDecisionOutput
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


class _CountingPlannerAgent:
    def __init__(self):
        self.calls = 0

    def run(self, state):
        self.calls += 1
        state.simulation_plan = SimulationPlan(
            name="fcc_al_iteration_test",
            summary="Iteration test plan.",
            workspace="fcc_al_iteration_test",
            material_id=state.selected_material_key or "fcc_al",
            outputs=["stress_strain_curve"],
            geometry=GeometrySpec(grid_type="voronoi", cells=[8, 8, 8], size=[1.0, 1.0, 1.0], grains=8),
            loading=LoadingSpec(mode="uniaxial_tension", direction="x", final_strain=0.02, strain_rate=1.0e-3, steps=5),
        )
        state.traces.append({"agent": "simulation_planner", "event": f"planned_{self.calls}", "details": {}})
        return state


class _LoopOnceIterationDecider:
    def __init__(self):
        self.calls = 0

    def run(self, state):
        self.calls += 1
        updated = dict(state)
        updated["iteration_decision"] = IterationDecisionOutput(
            continue_research=self.calls == 1,
            rationale="Loop once for test coverage." if self.calls == 1 else "Stop after the second planner pass.",
            next_focus="planner" if self.calls == 1 else None,
        )
        return append_trace(updated, "iteration_decider", f"iteration_decided_{self.calls}", {})


def test_langgraph_iteration_routes_back_to_planner(monkeypatch):
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

    planner = _CountingPlannerAgent()
    decider = _LoopOnceIterationDecider()

    final_state = run_research_graph(
        user_query="Study FCC aluminum under uniaxial tension",
        mode="dry_run",
        use_llm=False,
        model=None,
        max_iterations=2,
        allow_overwrite=True,
        checkpoint=False,
        agent_overrides={
            "simulation_planner": planner,
            "iteration_decider": decider,
        },
        stream=False,
    )

    assert planner.calls == 2
    assert final_state["iteration"] == 1
    assert final_state["report_path"] is not None
