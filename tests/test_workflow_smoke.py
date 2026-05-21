from damask_copilot.agents.project_planner import ProjectPlannerAgent
from damask_copilot.graph.workflow import run_workflow
from damask_copilot.llm.structured_runner import StructuredLLMRunner


def test_v1_workflow_smoke_runs_in_dry_run_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("DAMASK_COPILOT_LITERATURE_AUTO_SEARCH", "0")
    planner_runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "project_planner": {
                "project_objective": "Run a dry-run DAMASK workflow for Ni3Al",
                "research_questions": ["What is the first executable Ni3Al screening plan?"],
                "hypotheses": [
                    {
                        "id": "H1",
                        "statement": "A conservative Ni3Al DAMASK baseline can be generated and validated in dry-run mode.",
                        "evidence": ["workflow smoke goal"],
                        "validation_metric": "stress_strain_curve",
                        "type": "smoke_test",
                    }
                ],
                "evidence_status": [],
                "validation_metrics": ["stress_strain_curve"],
                "calibration_strategy": {"enabled": False},
                "candidate_simulations": [
                    {
                        "simulation_id": "SIM-1",
                        "title": "Smoke baseline",
                        "objective": "Create an executable smoke-test DAMASK baseline.",
                        "why_needed": "The workflow needs a minimal candidate simulation to proceed.",
                        "target_hypotheses": ["H1"],
                        "required_evidence": ["stress_strain_curve"],
                        "simulation_type_hint": "simulation_run",
                        "priority": 1,
                    }
                ],
                "stopping_criteria": ["Stop after the smoke-test pass is assembled."],
                "iteration_logic": ["Create one conservative candidate simulation."],
                "risks": ["Dry-run smoke tests do not validate physical fidelity."],
                "deliverables": ["Smoke-test planning artifact"],
                "next_action": "simulation_designer",
            }
        },
    )
    final_state = run_workflow(
        user_goal="Run a dry-run DAMASK workflow for Ni3Al",
        mode="dry_run",
        max_iterations=1,
        agent_overrides={
            "project_planner": ProjectPlannerAgent(use_llm=True, llm_runner=planner_runner),
        },
        state_overrides={
            "literature_files": [],
            "literature_sources": [],
            "experimental_files": [],
            "user_files": [],
            "workspace": str(tmp_path / "workflow_smoke"),
        },
    )

    assert final_state.final_report is not None or final_state.next_action is not None
    assert final_state.workspace is not None
