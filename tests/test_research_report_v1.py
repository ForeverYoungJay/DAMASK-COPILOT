from pathlib import Path

from damask_copilot.agents.research_report import ResearchReportAgent
from damask_copilot.graph.state import ResearchState


def test_research_report_v1_includes_scientific_sections(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    state = ResearchState(
        user_goal="Calibrate a DAMASK crystal plasticity model for Ni3Al using tensile stress-strain data.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        workspace=str(workspace),
        literature_summary={"summary": "Literature suggests strong orientation-sensitive slip in Ni3Al.", "sources": ["paper-a"]},
        known_parameters={
            "reported_cp_parameters": {"n_sl": 25.0},
            "elastic_constants": {"c11": 150e9, "c12": 90e9, "c44": 80e9},
        },
        damask_capabilities={"solver_features": ["grid_solver"], "execution_tools": ["run_damask_grid"]},
        project_plan={
            "project_objective": "Fit Ni3Al single-crystal tensile response.",
            "validation_metrics": ["rmse", "yield_stress_error"],
            "calibration_strategy": "Iteratively update slip resistance parameters.",
            "stopping_criteria": ["rmse < 20"],
            "candidate_simulations": [{"simulation_id": "SIM-1"}],
        },
        hypotheses=[{"id": "H1", "statement": "Slip resistance dominates the mismatch."}],
        simulation_spec={
            "task_type": "calibration",
            "constitutive_model": "phenopowerlaw",
            "geometry_strategy": "single_crystal",
            "loading_mode": "uniaxial_tension",
            "expected_observables": ["stress_strain"],
            "parameter_values": {"n_sl": 25.0, "xi_0_sl": 2.7e7},
            "parameter_ranges": {"n_sl": [15.0, 60.0]},
        },
        material_yaml_path=str(workspace / "material.yaml"),
        load_yaml_path=str(workspace / "load.yaml"),
        geometry_path=str(workspace / "geometry.vti"),
        numerics_yaml_path=str(workspace / "numerics.yaml"),
        validation_result={"ok": True, "warnings": [], "errors": []},
        run_result={"status": "success", "result_files": [str(workspace / "result.hdf5")], "failure_category": None},
        postprocessing_result={
            "status": "success",
            "curve": {"strain": [0.0, 0.01], "stress": [0.0, 100.0]},
        },
        experimental_data={"curve": {"strain": [0.0, 0.01], "stress": [0.0, 110.0]}},
        alignment_result={
            "status": "aligned",
            "summary": "Moderate mismatch remains.",
            "compared_observables": ["stress", "strain"],
            "metrics": {"rmse": 12.0, "max_abs_error": 20.0, "aligned_points": 25},
        },
        critique={
            "summary": "The model captures the trend but still underpredicts the flow stress.",
            "physical_validity": "preliminary",
            "confidence": "medium",
            "key_findings": ["Yield stress is underestimated."],
            "mismatch_analysis": {"severity": "moderate"},
            "limitations": ["Only one loading path was calibrated."],
            "recommended_actions": ["Update slip resistance parameters."],
        },
        next_action={"type": "update_parameters", "reason": "Calibration mismatch remains moderate."},
        parameter_history=[{"iteration": 0}],
        iteration=1,
    )

    updated = ResearchReportAgent().run(state)

    report_path = Path(updated.report_path)
    report_text = report_path.read_text(encoding="utf-8")

    assert "## Simulation Summary" in report_text
    assert "## Parameter Table" in report_text
    assert "## Experiment-Simulation Comparison" in report_text
    assert "## Scientific Interpretation" in report_text
    assert "## Limitations" in report_text
    assert "## Next-Step Recommendation" in report_text
    assert "stress_strain_comparison.png" in report_text
    assert "n_sl" in report_text
