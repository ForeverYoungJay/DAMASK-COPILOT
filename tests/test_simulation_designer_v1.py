from pathlib import Path

from damask_copilot.agents.simulation_designer import SimulationDesignerAgent
from damask_copilot.graph.state import ResearchState


def test_simulation_designer_v1_builds_concrete_simulation_task(tmp_path):
    state = ResearchState(
        user_goal="Calibrate a DAMASK crystal plasticity model for Ni3Al using tensile stress-strain data.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        project_name="ni3al_calibration",
        project_dir="projects/ni3al_calibration",
        mode="dry_run",
        workspace=str(tmp_path / "workspace"),
        project_plan={
            "validation_metrics": ["stress_strain_curve", "yield_stress"],
            "project_context": {
                "project_name": "ni3al_calibration",
                "project_dir": "projects/ni3al_calibration",
                "experimental_files": ["projects/ni3al_calibration/experimental/stress_strain.csv"],
                "literature_files": ["projects/ni3al_calibration/literature/paper.md"],
                "project_evidence": {"has_experimental_curve": True, "dataset_count": 1},
            },
            "parameter_priors": {
                "parameter_source": "data/materials/ni3al_l12_demo.yaml",
                "database_record": {"material_id": "ni3al_l12"},
                "reported_cp_parameters": {"type": "phenopowerlaw", "n_sl": [25], "h_0_sl-sl": [220e6]},
                "elastic_constants": {"C_11": 224e9, "C_12": 154e9, "C_44": 125e9},
                "phase_information": {"phase_name": "Ni3Al", "lattice": "cF"},
                "data_policy": {"future_backend": "sql_database"},
            },
            "candidate_simulations": [
                {
                    "simulation_id": "SIM-1",
                    "title": "Ni3Al calibration baseline",
                    "objective": "Match the tensile stress-strain curve.",
                    "why_needed": "Need a first calibration-ready baseline.",
                    "target_hypotheses": ["H1", "H2"],
                    "required_evidence": ["stress_strain_curve"],
                    "simulation_type_hint": "parameter_calibration",
                    "priority": 1,
                }
            ],
            "compute_budget": {
                "recommended_cells": [8, 8, 8],
                "recommended_grains": 4,
                "max_total_cells": 32 * 32 * 32,
            },
        },
        known_parameters={
            "phase_information": {"phase_name": "Ni3Al", "lattice": "cF"},
            "reported_cp_parameters": {"type": "phenopowerlaw", "n_sl": [25], "h_0_sl-sl": [220e6]},
            "elastic_constants": {"C_11": 224e9, "C_12": 154e9, "C_44": 125e9},
        },
        literature_summary={"summary": "Ordered-FCC slip is the main candidate mechanism."},
        experimental_data={"observable_candidates": ["stress_strain_curve", "yield_stress"]},
    )

    updated = SimulationDesignerAgent().run(state)

    assert updated.simulation_spec is not None
    assert updated.simulation_spec["task_type"] == "parameter_calibration"
    assert updated.simulation_spec["candidate_simulation"]["simulation_id"] == "SIM-1"
    assert updated.simulation_spec["validation_metrics"] == ["stress_strain_curve", "yield_stress"]
    assert updated.simulation_spec["project_context"]["project_dir"] == "projects/ni3al_calibration"
    assert updated.simulation_spec["parameter_priors"]["parameter_source"] == "data/materials/ni3al_l12_demo.yaml"
    assert updated.simulation_spec["input_data_contract"]["parameter_prior_source"].startswith("demo dataset")
    assert updated.simulation_spec["parameter_ranges"]
    assert updated.material_yaml_path is not None and Path(updated.material_yaml_path).exists()
    assert updated.load_yaml_path is not None and Path(updated.load_yaml_path).exists()
    assert updated.geometry_path is not None and Path(updated.geometry_path).exists()


def test_simulation_designer_v1_repairs_common_validation_errors(tmp_path):
    state = ResearchState(
        user_goal="Run a DAMASK simulation for Ni3Al.",
        workflow_type="simulation_run",
        material_system="ni3al_l12",
        mode="dry_run",
        workspace=str(tmp_path / "workspace"),
        project_plan={"validation_metrics": ["stress_strain_curve"], "candidate_simulations": []},
        known_parameters={
            "phase_information": {"phase_name": "Ni3Al", "lattice": "cF"},
            "reported_cp_parameters": {"n_sl": [25]},
            "elastic_constants": {"C_11": 224e9},
        },
    )
    state = SimulationDesignerAgent().run(state)
    state.validation_result = {
        "errors": [
            "Geometry/material mismatch: geometry references material index 1, but material.yaml defines only 1 material entry.",
            "phase 'Ni3Al' plastic block must define a 'type'.",
        ]
    }

    updated = SimulationDesignerAgent().repair_from_validation(state)

    assert updated.simulation_spec["material_indices"] == [0]
    assert updated.simulation_spec["plastic"]["type"] == "phenopowerlaw"
