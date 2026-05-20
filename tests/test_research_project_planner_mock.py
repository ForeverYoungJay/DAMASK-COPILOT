from damask_copilot.agents.research_project_planner import ResearchProjectPlannerAgent
from damask_copilot.llm.structured_runner import StructuredLLMRunner


def test_research_project_planner_supports_llm_mock():
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "research_project_planner": {
                "project_objective": "Build a staged project plan for Ni3Al rolling anisotropy.",
                "research_questions": ["What mechanism drives the anisotropy trend?"],
                "evidence_status": [
                    {
                        "topic": "Literature",
                        "status": "partial",
                        "evidence_summary": "Literature is suggestive but not yet sufficient for parameter transfer.",
                        "supporting_items": ["Paper A", "Paper B"],
                        "assumptions": ["Parameter transfer remains unverified"],
                    }
                ],
                "milestones": [
                    {
                        "milestone_id": "M1",
                        "title": "Frame the evidence",
                        "description": "Separate evidence-backed statements from assumptions.",
                        "evidence_needed": ["Literature", "Experimental metadata"],
                        "deliverables": ["Evidence map"],
                        "review_required": True,
                    }
                ],
                "deliverables": ["Project roadmap", "Candidate simulations"],
                "candidate_simulations": [
                    {
                        "simulation_id": "SIM-ROLL-1",
                        "title": "Rolling proxy screen",
                        "objective": "Test whether a rolling proxy can reproduce the anisotropy trend.",
                        "why_needed": "This is the first executable screen tied to the core research question.",
                        "target_hypotheses": ["H1"],
                        "required_evidence": ["Anisotropy trend"],
                        "simulation_type_hint": "plane_strain_rolling_proxy",
                        "priority": 1,
                    }
                ],
                "human_review_points": ["Approve the first candidate simulation before DAMASK input generation."],
                "risks": ["Experimental metadata are incomplete."],
                "success_criteria": ["One candidate simulation is clearly tied to a hypothesis."],
                "next_action": "human_review_framing",
            }
        },
    )
    agent = ResearchProjectPlannerAgent(use_llm=True, llm_runner=runner)

    updated = agent.run(
        {
            "user_query": "Study Ni3Al L12 rolling anisotropy",
            "use_llm": True,
            "model": None,
            "research_case": {"objective": "Explain rolling anisotropy in Ni3Al L12."},
            "research_questions": ["What mechanism drives anisotropy during rolling?"],
            "literature_review": {"summary": "Prior studies indicate orientation-sensitive slip."},
            "experimental_data_summary": {"summary": "One tensile dataset and one rolling metadata set are available."},
            "material_knowledge": {"summary": "L12 order constrains active systems."},
            "hypotheses": [{"id": "H1", "statement": "Orientation-sensitive slip drives anisotropy."}],
            "modeling_strategy": {"simulation_abstraction": "single_crystal"},
            "parameter_card": {"material_id": "ni3al_l12", "parameters": {"review_flags": ["low_confidence"]}},
            "human_feedback_history": [],
            "user_constraints": {"safety_constraints": ["Do not run without approval."]},
            "trace": [],
            "errors": [],
        }
    )

    assert updated["project_plan"].project_objective.startswith("Build a staged project plan")
    assert updated["candidate_simulations"][0].simulation_id == "SIM-ROLL-1"
    assert updated["selected_simulation_id"] == "SIM-ROLL-1"
    assert updated["project_milestones"] == ["M1"]
