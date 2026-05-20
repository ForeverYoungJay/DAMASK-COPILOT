from pathlib import Path

from damask_copilot.agents.research_report import ResearchReportAgent
from damask_copilot.schemas.project_plan import EvidenceStatus, ProjectMilestone, ProjectPlan


def test_research_report_includes_project_plan(tmp_path):
    agent = ResearchReportAgent()
    state = {
        "user_query": "Study Ni3Al L12 rolling anisotropy",
        "mode": "dry_run",
        "workspace": str(tmp_path / "workspace"),
        "research_case": {"material_system": "ni3al_l12"},
        "research_questions": ["What mechanism drives rolling anisotropy?"],
        "literature_review": {"status": "literature_review_ready", "summary": "Literature suggests orientation-sensitive slip."},
        "experimental_data_summary": {"status": "experimental_data_missing", "summary": "No direct rolling dataset yet."},
        "human_feedback_history": [],
        "hypotheses": [],
        "modeling_strategy": {},
        "project_plan": ProjectPlan(
            project_objective="Build a staged plan for explaining rolling anisotropy in Ni3Al L12.",
            research_questions=["What mechanism drives rolling anisotropy?"],
            evidence_status=[
                EvidenceStatus(
                    topic="Literature",
                    status="partial",
                    evidence_summary="The literature is informative but not sufficient for direct parameter transfer.",
                )
            ],
            milestones=[
                ProjectMilestone(
                    milestone_id="M1",
                    title="Evidence framing",
                    description="Separate evidence from assumptions.",
                    deliverables=["Evidence map"],
                    review_required=True,
                )
            ],
            deliverables=["Project roadmap", "Candidate simulation list"],
            human_review_points=["Confirm the first simulation before input generation."],
            risks=["No direct validation dataset is available yet."],
            success_criteria=["At least one candidate simulation is tied to the main research question."],
            next_action="human_review_framing",
        ),
        "project_milestones": ["M1"],
        "current_milestone": "M1",
        "selected_simulation_id": "SIM-1",
        "parameter_card": None,
        "simulation_plan": None,
        "generated_files": None,
        "run_report": None,
        "postprocess_report": None,
        "alignment_report": None,
        "critic_report": None,
        "trace": [],
        "errors": [],
    }

    updated = agent.run(state)
    report_text = Path(updated["report_path"]).read_text(encoding="utf-8")

    assert "## Project Plan" in report_text
    assert "Build a staged plan for explaining rolling anisotropy in Ni3Al L12." in report_text
    assert "Project roadmap" in report_text
    assert "Success criteria status: not_yet_met (planning_only)" in report_text
