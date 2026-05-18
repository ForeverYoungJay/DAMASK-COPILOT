from pathlib import Path

from damask_copilot.graph.runner import run_research_graph
from damask_copilot.llm.structured_runner import StructuredLLMRunner


def test_langgraph_dry_run_mock(monkeypatch):
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

    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "research_manager": {
                "material_system": "fcc_al",
                "objective": "Study response under uniaxial tension",
                "reasoning_summary": "The query names FCC aluminum under uniaxial tension.",
            },
            "literature_agent": {
                "literature_notes": ["Use a conservative smoke-test before physical interpretation."],
                "evidence_gaps": ["Literature-calibrated parameters are not loaded in this test."],
            },
            "material_knowledge": {
                "material_label": "FCC Aluminum Demo",
                "crystal_structure": "fcc",
                "knowledge_summary": "FCC aluminum is suitable for a low-cost first smoke test.",
                "planning_considerations": ["Keep the cell count small.", "Use stress_strain_curve output."],
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
                "summary": "The setup is appropriate for a dry-run smoke test.",
                "strengths": ["The plan is conservative."],
                "limitations": ["No numerical result exists in dry-run mode."],
                "next_steps": ["Enable smoke-test execution after reviewing the inputs."],
            },
            "iteration_decider": {
                "continue_research": False,
                "rationale": "One dry-run planning pass is enough for this test.",
                "next_focus": None,
            },
            "report_writer": {
                "title": "DAMASK Copilot Report",
                "executive_summary": "The graph completed a dry-run planning cycle without executing DAMASK.",
                "key_points": ["Goal parsed.", "Files generated.", "Checker passed."],
                "next_recommended_simulations": ["Enable smoke-test execution next."],
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

    assert final_state["approval_status"] == "not_required"
    assert final_state["run_report"] is None
    assert final_state["report_path"] is not None
    assert Path(final_state["report_path"]).exists()
    assert any(item["agent"] == "literature_agent" for item in final_state["trace"])
