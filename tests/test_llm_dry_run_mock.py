from pathlib import Path

from damask_copilot.graph.simple_runner import run_research_graph
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.research_state import ResearchState


def test_llm_dry_run_mock_generates_inputs_and_report(monkeypatch):
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

    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "research_manager": {
                "material_system": "fcc_al",
                "objective": "Study response under uniaxial tension",
                "reasoning_summary": "The query names FCC aluminum under tension.",
            },
            "material_knowledge": {
                "material_label": "FCC Aluminum Demo",
                "crystal_structure": "fcc",
                "knowledge_summary": "Use a conservative smoke-test plan.",
                "planning_considerations": ["Demo parameters are acceptable for smoke-test planning only."],
            },
            "simulation_planner": {
                "plan_name": "fcc_al_uniaxial_tension_smoke_test",
                "summary": "Conservative FCC aluminum tension smoke test.",
                "grid_type": "voronoi",
                "cells": [8, 8, 8],
                "size": [1.0, 1.0, 1.0],
                "grains": 8,
                "loading_mode": "uniaxial_tension",
                "loading_direction": "x",
                "final_strain": 0.02,
                "strain_rate": 1.0e-3,
                "steps": 5,
                "outputs": ["stress_strain_curve"],
            },
            "scientific_critic": {
                "summary": "The dry-run workflow generated conservative inputs without executing DAMASK.",
                "strengths": ["Input generation completed."],
                "limitations": ["No numerical results are available in dry-run mode."],
                "next_steps": ["Review generated files before enabling execution."],
            },
        },
    )

    state = ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        dry_run=True,
        use_llm=True,
    )

    final_state = run_research_graph(state, llm_runner=runner)

    assert final_state.generated_files is not None
    assert Path(final_state.generated_files.material_path).exists()
    assert Path(final_state.generated_files.load_path).exists()
    assert Path(final_state.generated_files.geometry_path).exists()
    assert Path(final_state.generated_files.research_state_path).exists()
    assert final_state.run_report is None
    assert final_state.checker_report is not None
    assert final_state.checker_report.ok is True
    assert Path(final_state.report_path).exists()
