from pathlib import Path

from damask_copilot.agents.human_review_agent import HumanReviewAgent
from damask_copilot.agents.hypothesis_agent import HypothesisAgent
from damask_copilot.agents.iteration_decision import IterationDecisionAgent
from damask_copilot.agents.modeling_strategy_agent import ModelingStrategyAgent
from damask_copilot.agents.research_report import ResearchReportAgent
from damask_copilot.graph.materials_research_nodes import build_materials_research_nodes
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.critic_report import CriticReport
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


def test_hypothesis_agent_supports_llm_mock():
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "hypothesis_agent": {
                "hypotheses": [
                    {
                        "id": "H1",
                        "statement": "Slip-mediated hardening controls the tensile response.",
                        "evidence": ["Literature indicates FCC slip activity."],
                        "required_simulation": "polycrystal_rve",
                        "expected_observable": "stress_strain_curve",
                        "risks": ["Parameters are low confidence."],
                    }
                ]
            }
        },
    )
    agent = HypothesisAgent(use_llm=True, llm_runner=runner)
    updated = agent.run(
        {
            "user_query": "Study FCC copper under uniaxial tension",
            "use_llm": True,
            "model": None,
            "research_case": {"loading_mode": "uniaxial_tension"},
            "literature_review": {"mechanisms": ["slip"]},
            "experimental_data_summary": {},
            "modeling_strategy": {"simulation_abstraction": "polycrystal_rve"},
            "material_knowledge": {},
            "trace": [],
            "errors": [],
        }
    )
    assert updated["hypotheses"][0]["id"] == "H1"


def test_modeling_strategy_agent_supports_llm_mock():
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "modeling_strategy_agent": {
                "simulation_abstraction": "polycrystal_rve",
                "geometry_strategy": "voronoi_rve",
                "loading_proxy": "uniaxial_tension",
                "target_grains": 12,
                "comparison_targets": ["stress_strain_curve"],
                "required_outputs": ["stress_strain_curve", "texture_evolution"],
                "assumptions": ["Use a small RVE for the first validation run."],
                "limitations": ["Parameters remain low confidence."],
                "requires_human_review": False,
            }
        },
    )
    agent = ModelingStrategyAgent(use_llm=True, llm_runner=runner)
    updated = agent.run(
        {
            "user_query": "Study FCC copper under uniaxial tension",
            "use_llm": True,
            "model": None,
            "research_case": {"loading_mode": "uniaxial_tension", "microstructure": "polycrystal"},
            "literature_review": {},
            "experimental_data_summary": {},
            "hypotheses": [],
            "trace": [],
            "errors": [],
        }
    )
    assert updated["modeling_strategy"]["target_grains"] == 12


def test_iteration_decision_agent_supports_llm_mock():
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "iteration_decider": {
                "action": "revise_modeling_strategy",
                "continue_research": True,
                "rationale": "The alignment suggests the abstraction should be revised.",
                "next_focus": "modeling_strategy",
            }
        },
    )
    agent = IterationDecisionAgent(use_llm=True, llm_runner=runner)
    updated = agent.run(
        {
            "user_query": "Study FCC copper under uniaxial tension",
            "use_llm": True,
            "model": None,
            "iteration": 0,
            "max_iterations": 2,
            "experimental_data_summary": {},
            "checker_report": None,
            "alignment_report": {"status": "comparison_not_possible"},
            "critic_report": None,
            "parameter_card": None,
            "trace": [],
            "errors": [],
        }
    )
    assert updated["iteration_decision"]["action"] == "revise_modeling_strategy"


def test_research_report_agent_supports_llm_mock(tmp_path):
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "research_report": {
                "title": "Copper Tension Research Report",
                "executive_summary": "This run establishes a smoke-test baseline for FCC copper.",
                "key_points": ["The workflow executed successfully."],
                "next_recommended_simulations": ["Calibrate parameters before quantitative use."],
            }
        },
    )
    agent = ResearchReportAgent(use_llm=True, llm_runner=runner)
    state = {
        "user_query": "Study FCC copper under uniaxial tension",
        "use_llm": True,
        "model": None,
        "workspace": str(tmp_path / "workspace"),
        "research_case": {"material_system": "fcc_cu"},
        "research_questions": [],
        "literature_review": {},
        "experimental_data_summary": {
            "status": "experimental_data_loaded",
            "summary": "Loaded one tensile dataset.",
            "observable_candidates": ["stress_strain_curve"],
            "semantic_column_guesses": {"strain (%)": "engineering_strain", "stress (MPa)": "engineering_stress"},
            "metadata_questions": ["Confirm whether stress is engineering or true stress."],
            "interpretation_summary": "The dataset appears to represent an engineering stress-strain curve.",
        },
        "human_feedback_history": [],
        "hypotheses": [],
        "modeling_strategy": {},
        "parameter_card": {
            "material_id": "fcc_cu",
            "material_name": "FCC Copper Demo",
            "confidence": "low",
            "is_demo_template": True,
            "parameters": {
                "parameter_sources": [{"source": "data/materials/fcc_cu_demo.yaml", "kind": "internal_template", "confidence": "low"}],
                "review_flags": ["template_parameters", "low_confidence"],
                "parameter_assessment": {
                    "suitability_summary": "Template parameters are suitable only for smoke tests.",
                    "likely_mismatches": ["Hardening is not calibrated to the target copper condition."],
                    "assumption_risks": ["Quantitative interpretation would be unsafe."],
                    "recommended_checks": ["Replace with calibrated copper parameters."],
                    "requires_human_review": True,
                },
            },
        },
        "simulation_plan": None,
        "generated_files": None,
        "run_report": None,
        "postprocess_report": None,
        "alignment_report": {
            "status": "aligned",
            "summary": "Curves were aligned at the metadata level.",
            "compared_observables": ["stress", "strain"],
            "metrics": {"rmse": 12.5, "mae": 10.0, "comparison_points": 3},
            "llm_interpretation": {
                "summary": "The simulation appears slightly stiffer than the experiment.",
                "likely_mismatch_causes": ["Template hardening may be too strong."],
                "recommended_actions": ["Calibrate the slip hardening law."],
                "confidence": "medium",
            },
            "notes": ["Units still need confirmation."],
            "requires_human_review": False,
        },
        "critic_report": None,
        "trace": [],
        "errors": [],
    }
    updated = agent.run(state)
    report_text = Path(updated["report_path"]).read_text(encoding="utf-8")
    assert "## Executive Summary" in report_text
    assert "Copper Tension Research Report" in report_text
    assert "Semantic column guesses" in report_text
    assert "Parameter assessment" in report_text
    assert "Deterministic metrics" in report_text
    assert "LLM interpretation" in report_text


def test_research_report_agent_formats_missing_experiment_and_dedupes_steps(tmp_path):
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "research_report": {
                "title": "FCC Al Planning Report",
                "executive_summary": "Dry-run planning report.",
                "key_points": ["No experiment was required for this planning pass."],
                "next_recommended_simulations": [
                    "Run 16^3 vs 32^3 grid comparison.",
                    "Run a 16^3 versus 32^3 grid comparison.",
                ],
            }
        },
    )
    agent = ResearchReportAgent(use_llm=True, llm_runner=runner)
    state = {
        "user_query": "Study FCC Al under uniaxial tension",
        "use_llm": True,
        "model": None,
        "mode": "dry_run",
        "workspace": str(tmp_path / "workspace"),
        "research_case": {"material_system": "fcc_al"},
        "research_questions": [],
        "literature_review": {"status": "literature_missing", "summary": "No directly relevant literature was supplied."},
        "experimental_data_summary": {
            "status": "experimental_data_missing",
            "summary": "No experimental datasets were supplied.",
            "observable_candidates": [],
        },
        "human_feedback_history": [],
        "hypotheses": [],
        "modeling_strategy": {},
        "parameter_card": None,
        "simulation_plan": None,
        "generated_files": None,
        "run_report": None,
        "postprocess_report": None,
        "alignment_report": None,
        "critic_report": CriticReport(
            summary="Planning-only critique.",
            limitations=["No experimental validation data are available."],
            next_steps=["Run 16^3 vs 32^3 grid comparison."],
        ),
        "trace": [],
        "errors": [],
    }

    updated = agent.run(state)
    report_text = Path(updated["report_path"]).read_text(encoding="utf-8")
    assert "This is acceptable for exploratory or hypothesis-driven plans" in report_text
    assert "Run report status: skipped_due_to_dry_run" in report_text
    assert "Status: not_applicable" in report_text
    assert "Compared observables: None" in report_text
    final_steps = report_text.split("## Final Claims and Next Steps", 1)[1]
    assert final_steps.count("- Run 16^3 vs 32^3 grid comparison.") == 1


def test_human_review_after_critique_not_required_for_dry_run_without_alignment_issue():
    agent = HumanReviewAgent("human_review_after_critique")
    updated = agent.run(
        {
            "mode": "dry_run",
            "human_review_policy": {"after_critique_review": False},
            "alignment_report": {"status": "not_applicable", "requires_human_review": False},
            "experimental_data_summary": {"status": "experimental_data_missing", "needs_human_correction": False},
            "parameter_card": {"parameters": {"review_flags": ["template_parameters"]}},
            "critic_report": CriticReport(summary="Planning critique.", limitations=["Low confidence parameters."]),
            "human_feedback_history": [],
            "trace": [],
            "errors": [],
        }
    )
    assert updated["pending_human_review"] is None
    assert updated["human_feedback_history"] == []


def test_simulation_planner_syncs_strategy_target_grains_with_executable_plan():
    class _FakePlanner:
        def run(self, state):
            state.simulation_plan = SimulationPlan(
                name="fcc_al_plan",
                summary="Executable screening plan.",
                workspace="fcc_al_plan",
                material_id="fcc_al",
                outputs=["stress_strain_curve"],
                geometry=GeometrySpec(grid_type="voronoi", cells=[16, 16, 16], size=[1.0, 1.0, 1.0], grains=16),
                loading=LoadingSpec(mode="uniaxial_tension", direction="x", final_strain=0.03, strain_rate=1.0e-3, steps=30),
            )
            state.goal = ResearchGoal(user_query=state.user_query, material_system="fcc_al", objective="Study FCC Al under tension")
            return state

    nodes = build_materials_research_nodes(agent_overrides={"simulation_planner": _FakePlanner()})
    updated = nodes["simulation_planner"](
        {
            "user_query": "Study FCC Al under uniaxial tension",
            "mode": "dry_run",
            "use_llm": False,
            "model": None,
            "research_case": {"material_system": "fcc_al", "loading_mode": "uniaxial_tension"},
            "modeling_strategy": {
                "simulation_abstraction": "polycrystal_rve",
                "target_grains": 100,
                "required_outputs": ["stress_strain_curve"],
                "comparison_targets": ["stress_strain_curve"],
                "assumptions": [],
            },
            "trace": [],
            "errors": [],
        }
    )
    assert updated["simulation_plan"].geometry.grains == 16
    assert updated["modeling_strategy"]["target_grains"] == 16
    assert updated["modeling_strategy"]["recommended_follow_on_grains"] == 100
