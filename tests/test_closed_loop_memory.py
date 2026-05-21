from damask_copilot.agents.analysis_critic import AnalysisAndCriticAgent
from damask_copilot.agents.simulation_designer import SimulationDesignerAgent
from damask_copilot.graph.state import ResearchState
from damask_copilot.memory.scientific_memory import ScientificMemoryLayer


def test_simulation_designer_and_analysis_critic_write_to_shared_memory(tmp_path):
    shared_memory = ScientificMemoryLayer(workspace_root=tmp_path / "workspaces")
    state = ResearchState(
        user_goal="Calibrate Ni3Al DAMASK parameters from tensile data.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        mode="full_run",
        workspace=str(tmp_path / "workspace"),
        project_plan={
            "validation_metrics": ["stress_strain_curve", "yield_stress"],
            "candidate_simulations": [{"simulation_id": "SIM-1", "simulation_type_hint": "parameter_calibration", "priority": 1}],
            "compute_budget": {"recommended_cells": [8, 8, 8], "recommended_grains": 4},
        },
        known_parameters={
            "phase_information": {"phase_name": "Ni3Al", "lattice": "cF"},
            "reported_cp_parameters": {"type": "phenopowerlaw", "n_sl": [25], "xi_0_sl": [2.7e7]},
            "elastic_constants": {"C_11": 224e9},
        },
        experimental_data={"curve": {"strain": [0.0, 0.01], "stress": [0.0, 100.0]}},
    )

    state = SimulationDesignerAgent(scientific_memory=shared_memory).run(state)
    state.validation_result = {"ok": True, "errors": [], "warnings": []}
    state.run_result = {"status": "success", "failure_category": None, "result_files": ["result.hdf5"]}
    state.postprocessing_result = {
        "ok": True,
        "status": "success",
        "yield_stress": {"ok": True, "yield_stress": 180.0, "strain_at_yield": 0.002},
        "hardening_rate": {"ok": True, "hardening_rate": 1800.0},
        "comparison": {"ok": True, "rmse": 55.0, "max_abs_error": 70.0, "aligned_points": 25},
    }

    updated = AnalysisAndCriticAgent(scientific_memory=shared_memory).run(state)
    result_db = shared_memory.collect_context(material_system="ni3al_l12")["simulation_result_database"]

    stages = {entry["stage"] for entry in result_db}
    assert "design" in stages
    assert "analysis" in stages
    assert updated.next_action["type"] == "update_parameters"
    assert shared_memory.collect_context(material_system="ni3al_l12")["optimization_history"]


def test_analysis_critic_writes_validation_and_error_fix_memory(tmp_path):
    shared_memory = ScientificMemoryLayer(workspace_root=tmp_path / "workspaces")
    state = ResearchState(
        user_goal="Run Ni3Al DAMASK simulation.",
        workflow_type="simulation_run",
        material_system="ni3al_l12",
        mode="full_run",
        validation_result={"ok": False, "errors": ["material index out of bounds"], "warnings": []},
        run_result={"status": "failed", "failure_category": "model", "error": "material index out of bounds"},
        postprocessing_result={"ok": False, "status": "not_available", "error": "No result files were available."},
        experimental_data={"curve": {"strain": [0.0, 0.01], "stress": [0.0, 100.0]}},
    )

    AnalysisAndCriticAgent(scientific_memory=shared_memory).run(state)
    error_db = shared_memory.collect_context(material_system="ni3al_l12")["error_fix_database"]

    assert any(item["failure_category"] == "model" for item in error_db)
    assert any(item["failure_category"] == "validation" for item in error_db)
