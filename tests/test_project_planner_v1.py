from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.agents.project_planner import ProjectPlannerAgent
from damask_copilot.graph.state import ResearchState


def test_project_planner_v1_builds_scientific_project_plan():
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "project_planner": {
                "project_objective": "Calibrate a DAMASK crystal plasticity model against target observables.",
                "research_questions": [
                    "Which Ni3Al tensile observable should anchor the first calibration loop?",
                    "Which constitutive assumptions are sufficiently supported to justify the first DAMASK screening plan?",
                ],
                "hypotheses": [
                    {
                        "id": "H1",
                        "statement": "A slip-mediated DAMASK model can reproduce the dominant tensile response trend for Ni3Al.",
                        "evidence": ["ordered-FCC slip", "hardening evolution"],
                        "validation_metric": "stress_strain_curve",
                        "type": "baseline_reproducibility",
                    }
                ],
                "evidence_status": [
                    {
                        "topic": "literature",
                        "status": "partial",
                        "evidence_summary": "Literature supports mechanism-level planning but parameter transfer remains uncertain.",
                        "supporting_items": ["ordered-FCC slip", "hardening evolution"],
                        "assumptions": ["Published transferable parameters are uncertain."],
                    }
                ],
                "validation_metrics": ["stress_strain_curve", "yield_stress"],
                "calibration_strategy": {
                    "enabled": True,
                    "objective": "Tune CP parameters against experimental observables.",
                    "target_metrics": ["stress_strain_curve", "yield_stress"],
                },
                "candidate_simulations": [
                    {
                        "simulation_id": "SIM-1",
                        "title": "Ni3Al tensile baseline",
                        "objective": "Establish the first calibration-ready DAMASK tensile baseline.",
                        "why_needed": "The first executable simulation should test the leading tensile hypothesis.",
                        "target_hypotheses": ["H1"],
                        "required_evidence": ["stress_strain_curve"],
                        "simulation_type_hint": "parameter_calibration",
                        "priority": 1,
                    }
                ],
                "stopping_criteria": [
                    "Stop when the leading tensile observable is sufficiently matched.",
                ],
                "iteration_logic": [
                    "Start from the leading tensile observable and expand only if mismatch remains.",
                ],
                "risks": ["Published transferable parameters are uncertain."],
                "deliverables": ["Scientific project roadmap", "Candidate DAMASK simulation plan outline"],
                "next_action": "simulation_designer",
            }
        },
    )
    state = ResearchState(
        user_goal="Calibrate a DAMASK crystal plasticity model for Ni3Al using tensile stress-strain data.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        project_name="ni3al_calibration",
        project_dir="projects/ni3al_calibration",
        objective="Calibrate a DAMASK crystal plasticity model against target observables.",
        needs_parameter_optimization=True,
        max_iterations=3,
        mode="dry_run",
        literature_files=["projects/ni3al_calibration/literature/paper.md"],
        experimental_files=["projects/ni3al_calibration/experimental/stress_strain.csv"],
        literature_summary={
            "summary": "Literature suggests ordered-FCC slip controls tensile response.",
            "mechanisms": ["ordered-FCC slip", "hardening evolution"],
            "evidence_gaps": ["Published transferable parameters are uncertain."],
            "planning_evidence": {
                "mechanisms": ["ordered-FCC slip", "hardening evolution"],
                "planning_implications": ["Use tensile stress-strain calibration before broader parametric sweeps."],
                "observables_for_validation": ["stress_strain_curve", "yield_stress"],
                "experimental_conditions": ["uniaxial_tension"],
            },
        },
        experimental_data={
            "summary": "One tensile stress-strain dataset is available.",
            "observable_candidates": ["stress_strain_curve", "yield_stress"],
            "curve": {"strain": [0.0, 0.01], "stress": [0.0, 100.0]},
            "metadata_questions": ["Temperature metadata should be confirmed."],
        },
        known_parameters={
            "source": "data/materials/ni3al_l12_demo.yaml",
            "confidence": "low",
            "reported_cp_parameters": {"type": "phenopowerlaw", "n_sl": [25]},
            "elastic_constants": {"C_11": 224e9, "C_12": 154e9, "C_44": 125e9},
            "phase_information": {"phase_name": "Ni3Al", "lattice": "cF"},
            "scientific_memory_context": {
                "cp_parameter_database": {
                    "material_id": "ni3al_l12",
                    "source_path": "data/materials/ni3al_l12_demo.yaml",
                }
            },
        },
        damask_capabilities={
            "preprocess_tools": ["build_material_yaml"],
            "execution_tools": ["run_damask_grid"],
            "postprocess_tools": ["extract_stress_strain"],
            "documentation_sources": [{"path": "README.md", "matched": True}],
        },
    )

    updated = ProjectPlannerAgent(use_llm=True, llm_runner=runner).run(state)

    assert updated.hypotheses
    assert updated.project_plan is not None
    assert updated.project_plan["workflow_type"] == "calibration"
    assert updated.project_plan["validation_metrics"] == ["stress_strain_curve", "yield_stress"]
    assert updated.project_plan["calibration_strategy"]["enabled"] is True
    assert updated.project_plan["candidate_simulations"]
    assert updated.project_plan["compute_budget"]["max_total_cells"] > 0
    assert updated.project_plan["stopping_criteria"]
    assert updated.project_plan["project_context"]["project_dir"] == "projects/ni3al_calibration"
    assert updated.project_plan["project_context"]["project_evidence"]["has_experimental_curve"] is True
    assert updated.project_plan["project_context"]["project_evidence"]["literature_planning_evidence"]["observables_for_validation"] == [
        "stress_strain_curve",
        "yield_stress",
    ]
    assert updated.project_plan["parameter_priors"]["data_policy"]["future_backend"] == "sql_database"
    assert updated.project_plan["parameter_priors"]["demo_dataset_source"] == "data/materials/ni3al_l12_demo.yaml"


def test_project_planner_v1_supports_llm_mock():
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "project_planner": {
                "project_objective": "Calibrate Ni3Al crystal plasticity with specimen-aware tensile evidence.",
                "research_questions": [
                    "Which parameters most strongly control the initial yield offset for the single-crystal tensile specimens?",
                    "Should the first calibration stage focus on xi_0_sl before broad hardening re-tuning?",
                ],
                "hypotheses": [
                    {
                        "id": "H1",
                        "statement": "The tensile mismatch is dominated by initial slip resistance rather than latent hardening saturation.",
                        "evidence": ["Single-crystal tensile curves", "Ni3Al literature planning evidence"],
                        "validation_metric": "stress_strain_curve",
                        "type": "parameter_calibration",
                    }
                ],
                "evidence_status": [
                    {
                        "topic": "literature",
                        "status": "partial",
                        "evidence_summary": "Literature supports slip-mediated planning but not direct parameter transfer.",
                        "supporting_items": ["Ni3Al planning note"],
                        "assumptions": ["Parameter priors remain low confidence"],
                    }
                ],
                "validation_metrics": ["stress_strain_curve", "yield_stress"],
                "calibration_strategy": {
                    "enabled": True,
                    "objective": "Tune xi_0_sl first, then hardening parameters if needed.",
                    "target_metrics": ["stress_strain_curve", "yield_stress"],
                },
                "candidate_simulations": [
                    {
                        "simulation_id": "SIM-SCT-1",
                        "title": "Single-crystal tensile baseline",
                        "objective": "Match the leading tensile specimen curve before multi-specimen expansion.",
                        "why_needed": "This isolates the first calibration step to the most relevant specimen-level observable.",
                        "target_hypotheses": ["H1"],
                        "required_evidence": ["stress_strain_curve"],
                        "simulation_type_hint": "single_crystal_tensile_calibration",
                        "priority": 1,
                    }
                ],
                "stopping_criteria": [
                    "Stop when tensile curve mismatch is no longer dominated by the initial yield offset.",
                ],
                "iteration_logic": [
                    "Run the single-crystal tensile baseline first.",
                    "Update xi_0_sl before expanding to broader hardening changes.",
                ],
                "risks": ["Literature support for direct parameter transfer remains weak."],
                "deliverables": ["Specimen-aware calibration roadmap"],
                "next_action": "simulation_designer",
            }
        },
    )
    state = ResearchState(
        user_goal="Calibrate xi_0_sl for Ni3Al using single tensile stress-strain data.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        project_name="ni3al_l12",
        project_dir="projects/ni3al_l12",
        use_llm=True,
        literature_summary={
            "summary": "Literature suggests slip-mediated planning guidance.",
            "planning_evidence": {
                "mechanisms": ["slip-mediated plasticity"],
                "observables_for_validation": ["stress_strain_curve"],
                "planning_implications": ["Start from single-crystal tensile calibration."],
            },
        },
        experimental_data={
            "summary": "Single-crystal tensile specimens are available.",
            "observable_candidates": ["stress_strain_curve", "yield_stress"],
        },
        known_parameters={
            "source": "data/materials/ni3al_l12_demo.yaml",
            "reported_cp_parameters": {"type": "phenopowerlaw", "xi_0_sl": [120e6]},
            "elastic_constants": {"C_11": 224e9},
            "phase_information": {"phase_name": "Ni3Al", "lattice": "cF"},
        },
        damask_capabilities={
            "preprocess_tools": ["build_material_yaml"],
            "execution_tools": ["run_damask_grid"],
            "postprocess_tools": ["extract_stress_strain"],
            "documentation_sources": [{"path": "README.md", "matched": True}],
        },
    )

    updated = ProjectPlannerAgent(use_llm=True, llm_runner=runner).run(state)

    assert updated.project_plan["project_objective"].startswith("Calibrate Ni3Al crystal plasticity")
    assert updated.project_plan["research_questions"][0].startswith("Which parameters most strongly control")
    assert updated.hypotheses[0]["statement"].startswith("The tensile mismatch is dominated")
    assert updated.project_plan["candidate_simulations"][0]["simulation_id"] == "SIM-SCT-1"


def test_project_planner_v1_requires_llm():
    state = ResearchState(
        user_goal="Calibrate xi_0_sl for Ni3Al using single tensile stress-strain data.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        use_llm=False,
    )

    try:
        ProjectPlannerAgent(use_llm=False).run(state)
    except RuntimeError as exc:
        assert "LLM-only" in str(exc)
    else:
        raise AssertionError("ProjectPlannerAgent should require an LLM runner.")
