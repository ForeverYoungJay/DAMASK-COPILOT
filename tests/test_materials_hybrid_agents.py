import csv
from pathlib import Path

from damask_copilot.agents.experiment_simulation_alignment import ExperimentSimulationAlignmentAgent
from damask_copilot.agents.experimental_data_agent import ExperimentalDataAgent
from damask_copilot.agents.parameter_agent import ParameterAgent
from damask_copilot.llm.structured_runner import StructuredLLMRunner


def test_experimental_data_agent_hybrid_adds_semantic_interpretation(tmp_path):
    csv_path = tmp_path / "exp.csv"
    csv_path.write_text("strain (%),stress (MPa)\n0.0,0.0\n1.0,100.0\n", encoding="utf-8")
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "experimental_data_agent": {
                "semantic_column_guesses": {"strain (%)": "engineering_strain", "stress (MPa)": "engineering_stress"},
                "likely_observables": ["stress_strain_curve"],
                "metadata_questions": [],
                "interpretation_summary": "Columns appear to describe an engineering stress-strain curve.",
            }
        },
    )
    agent = ExperimentalDataAgent(use_llm=True, llm_runner=runner)
    state = {
        "user_query": "Compare copper tension against experiment",
        "use_llm": True,
        "model": None,
        "experimental_files": [str(csv_path)],
        "user_files": [],
        "trace": [],
        "errors": [],
    }

    updated = agent.run(state)
    summary = updated["experimental_data_summary"]
    assert summary["status"] == "experimental_data_loaded"
    assert summary["semantic_column_guesses"]["strain (%)"] == "engineering_strain"
    assert "stress_strain_curve" in summary["observable_candidates"]


def test_parameter_agent_hybrid_adds_parameter_assessment():
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "parameter_agent": {
                "suitability_summary": "Template parameters are acceptable only for smoke tests.",
                "likely_mismatches": ["No literature-backed hardening calibration is available."],
                "assumption_risks": ["Quantitative claims are not justified with this parameter card."],
                "recommended_checks": ["Replace with calibrated copper parameters before production use."],
                "requires_human_review": True,
            }
        },
    )
    agent = ParameterAgent(use_llm=True, llm_runner=runner)
    state = {
        "user_query": "Study FCC copper under uniaxial tension",
        "use_llm": True,
        "model": None,
        "research_case": {"material_system": "fcc_cu", "structure": "fcc"},
        "literature_review": {},
        "modeling_strategy": {"simulation_abstraction": "polycrystal_rve"},
        "user_constraints": {},
        "trace": [],
        "errors": [],
    }

    updated = agent.run(state)
    params = updated["parameter_card"].parameters
    assert "parameter_assessment" in params
    assert "llm_review_required" in params["review_flags"]


def test_alignment_agent_hybrid_adds_interpretation(tmp_path):
    exp_path = tmp_path / "exp.csv"
    sim_path = tmp_path / "sim.csv"
    exp_rows = [
        {"strain": "0.0", "stress": "0.0"},
        {"strain": "0.01", "stress": "90.0"},
        {"strain": "0.02", "stress": "110.0"},
    ]
    sim_rows = [
        {"strain": "0.0", "stress": "0.0"},
        {"strain": "0.01", "stress": "100.0"},
        {"strain": "0.02", "stress": "120.0"},
    ]
    for path, rows in ((exp_path, exp_rows), (sim_path, sim_rows)):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["strain", "stress"])
            writer.writeheader()
            writer.writerows(rows)

    class _Postprocess:
        stress_strain_csv = str(sim_path)

    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "experiment_simulation_alignment": {
                "summary": "The simulated curve is slightly stiffer than the experimental curve.",
                "likely_mismatch_causes": ["Template hardening may be too strong."],
                "recommended_actions": ["Calibrate slip resistance and hardening parameters."],
                "confidence": "medium",
            }
        },
    )
    agent = ExperimentSimulationAlignmentAgent(use_llm=True, llm_runner=runner)
    state = {
        "user_query": "Align copper tension simulation with experiment",
        "use_llm": True,
        "model": None,
        "experimental_data_summary": {
            "status": "experimental_data_loaded",
            "datasets": [{"path": str(exp_path), "format": "csv", "columns": ["strain", "stress"]}],
        },
        "postprocess_report": _Postprocess(),
        "simulation_plan": {"name": "test"},
        "trace": [],
        "errors": [],
    }

    updated = agent.run(state)
    alignment = updated["alignment_report"]
    assert alignment["status"] == "aligned"
    assert "rmse" in alignment["metrics"]
    assert alignment["llm_interpretation"]["confidence"] == "medium"
