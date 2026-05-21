from damask_copilot.agents.analysis_critic import AnalysisAndCriticAgent
from damask_copilot.graph.state import ResearchState


def test_analysis_critic_v1_stops_for_good_alignment():
    state = ResearchState(
        user_goal="Compare a DAMASK Ni3Al simulation against tensile data.",
        workflow_type="experiment_simulation_comparison",
        mode="full_run",
        iteration=0,
        max_iterations=3,
        material_system="ni3al_l12",
        experimental_data={"curve": {"strain": [0.0, 0.01], "stress": [0.0, 100.0]}},
        run_result={"status": "success", "failure_category": None},
        postprocessing_result={
            "ok": True,
            "status": "success",
            "yield_stress": {"ok": True, "yield_stress": 120.0, "strain_at_yield": 0.002},
            "hardening_rate": {"ok": True, "hardening_rate": 2500.0},
            "comparison": {"ok": True, "rmse": 8.0, "max_abs_error": 12.0, "aligned_points": 25},
        },
    )

    updated = AnalysisAndCriticAgent().run(state)

    assert updated.alignment_result["status"] == "aligned"
    assert updated.critique["confidence"] == "high"
    assert updated.next_action["type"] == "stop"
    assert updated.iteration_decision["action"] == "finish"


def test_analysis_critic_v1_requests_parameter_update_for_calibration_mismatch():
    state = ResearchState(
        user_goal="Calibrate a DAMASK crystal plasticity model for Ni3Al.",
        workflow_type="calibration",
        mode="full_run",
        iteration=0,
        max_iterations=3,
        material_system="ni3al_l12",
        experimental_data={"curve": {"strain": [0.0, 0.01], "stress": [0.0, 100.0]}},
        simulation_spec={"parameter_values": {"n_sl": 25.0, "xi_0_sl": 2.7e7}},
        run_result={"status": "success", "failure_category": None},
        postprocessing_result={
            "ok": True,
            "status": "success",
            "yield_stress": {"ok": True, "yield_stress": 180.0, "strain_at_yield": 0.002},
            "hardening_rate": {"ok": True, "hardening_rate": 1800.0},
            "comparison": {"ok": True, "rmse": 55.0, "max_abs_error": 70.0, "aligned_points": 25},
        },
    )

    updated = AnalysisAndCriticAgent().run(state)

    assert updated.next_action["type"] == "update_parameters"
    assert updated.iteration_decision["continue_research"] is True
    assert updated.critique["objective_update"]["target"] == "rmse"
    assert updated.critique["postprocess_backend"] == "damask_postprocess_mcp_via_tool"


def test_analysis_critic_v1_requests_human_review_when_alignment_not_possible():
    state = ResearchState(
        user_goal="Compare DAMASK output with experiment.",
        workflow_type="experiment_simulation_comparison",
        mode="full_run",
        iteration=0,
        max_iterations=2,
        experimental_data={"curve": {"strain": [0.0, 0.01], "stress": [0.0, 100.0]}},
        run_result={"status": "success", "failure_category": None},
        postprocessing_result={"ok": False, "status": "not_available", "error": "No result files were available."},
    )

    updated = AnalysisAndCriticAgent().run(state)

    assert updated.alignment_result["status"] == "comparison_not_possible"
    assert updated.next_action["type"] == "request_human_review"
    assert updated.iteration_decision["action"] == "request_human_input"
