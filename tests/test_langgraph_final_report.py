from pathlib import Path

from damask_copilot.graph.runner import run_research_graph
from damask_copilot.llm.structured_runner import StructuredLLMRunner


def test_langgraph_final_report_contains_expected_sections(monkeypatch):
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
                "reasoning_summary": "FCC aluminum tension study.",
            },
            "literature_agent": {
                "literature_notes": ["Use a conservative plan."],
                "evidence_gaps": ["Validated literature parameters are not part of this mock."],
            },
            "material_knowledge": {
                "material_label": "FCC Aluminum Demo",
                "crystal_structure": "fcc",
                "knowledge_summary": "Use a low-cost first run.",
                "planning_considerations": ["Keep the grid small."],
            },
            "simulation_planner": {
                "plan_name": "fcc_al_langgraph_report_test",
                "summary": "Conservative dry-run plan.",
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
                "summary": "Dry-run planning is coherent.",
                "strengths": ["Checker passed."],
                "limitations": ["No numerical results are available."],
                "next_steps": ["Move to smoke-test execution next."],
            },
            "iteration_decider": {
                "continue_research": False,
                "rationale": "One dry-run pass is sufficient.",
                "next_focus": None,
            },
            "report_writer": {
                "title": "DAMASK Copilot Report",
                "executive_summary": "This report summarizes a LangGraph dry-run.",
                "key_points": ["Goal parsed.", "Inputs generated.", "Execution skipped."],
                "next_recommended_simulations": ["Run a smoke test next."],
            },
        },
    )

    final_state = run_research_graph(
        user_query="Study FCC aluminum under uniaxial tension",
        mode="dry_run",
        use_llm=True,
        model=None,
        max_iterations=1,
        allow_overwrite=True,
        checkpoint=False,
        llm_runner=runner,
        stream=False,
    )

    report_path = Path(final_state["report_path"])
    report_text = report_path.read_text(encoding="utf-8")

    assert "## Executive Summary" in report_text
    assert "## Research Goal" in report_text
    assert "## Scientific Critique" in report_text
    assert final_state["final_report"] is not None
