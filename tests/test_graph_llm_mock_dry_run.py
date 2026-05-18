from pathlib import Path

from damask_copilot.graph.simple_runner import run_research_graph
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.research_state import ResearchState


def test_graph_llm_mock_dry_run_writes_report():
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "research_manager": {
                "material_system": "fcc_al",
                "objective": "Study response under uniaxial tension",
                "reasoning_summary": "The query names FCC Al under tension.",
            },
            "material_knowledge": {
                "material_label": "FCC Aluminum Demo",
                "crystal_structure": "fcc",
                "knowledge_summary": "Use a low-cost initial plan.",
                "planning_considerations": ["Keep the cell count small."],
            },
            "simulation_planner": {
                "plan_name": "fcc_al_smoke_test",
                "summary": "Small tension smoke test.",
                "grid_type": "voronoi",
                "cells": [8, 8, 8],
                "size": [1.0, 1.0, 1.0],
                "grains": 8,
                "loading_mode": "uniaxial_tension",
                "loading_direction": "x",
                "final_strain": 0.02,
                "strain_rate": 1.0e-3,
                "steps": 5,
            },
            "scientific_critic": {
                "summary": "The workflow is coherent for a dry-run smoke test.",
                "strengths": ["The checker remains deterministic."],
                "limitations": ["No numerical results are available in dry-run mode."],
                "next_steps": ["Connect real MCP-backed generation later."],
            },
            "report_writer": {
                "title": "DAMASK Copilot Report",
                "executive_summary": "Mock dry-run summary.",
                "key_points": ["Inputs were planned conservatively."],
                "next_recommended_simulations": ["Enable MCP-backed generation next."],
            },
        },
    )
    state = ResearchState(
        user_query="Study FCC Al under uniaxial tension",
        dry_run=True,
        use_llm=True,
        smoke_test=True,
        overwrite=True,
    )

    final_state = run_research_graph(state, llm_runner=runner)

    assert final_state.material_knowledge_output is not None
    assert final_state.simulation_planner_output is not None
    assert final_state.checker_report is not None
    assert final_state.checker_report.ok is True
    assert final_state.report_path is not None
    assert Path(final_state.report_path).exists()
    assert "DAMASK Copilot Report" in Path(final_state.report_path).read_text(encoding="utf-8")
