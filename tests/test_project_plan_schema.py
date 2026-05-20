from damask_copilot.schemas.project_plan import (
    CandidateSimulation,
    EvidenceStatus,
    ProjectMilestone,
    ProjectPlan,
)


def test_project_plan_schema_round_trip():
    plan = ProjectPlan(
        project_objective="Build a staged Ni3Al research roadmap.",
        research_questions=["What controls anisotropy during rolling?"],
        evidence_status=[
            EvidenceStatus(
                topic="Literature",
                status="partial",
                evidence_summary="Literature suggests slip-driven anisotropy, but parameter transfer is still uncertain.",
                supporting_items=["Two relevant papers"],
                assumptions=["Transferability of published parameters is unproven"],
            )
        ],
        milestones=[
            ProjectMilestone(
                milestone_id="M1",
                title="Frame evidence",
                description="Separate knowns from assumptions.",
                evidence_needed=["Literature summary", "Experimental metadata"],
                deliverables=["Evidence table"],
                review_required=True,
            )
        ],
        deliverables=["Roadmap", "Candidate simulation list"],
        candidate_simulations=[
            CandidateSimulation(
                simulation_id="SIM-1",
                title="Rolling proxy screen",
                objective="Screen whether a rolling proxy can explain the anisotropy trend.",
                why_needed="This is the lowest-cost simulation that addresses the top hypothesis.",
                target_hypotheses=["H1"],
                required_evidence=["Stress-strain trend"],
                simulation_type_hint="plane_strain_rolling_proxy",
                priority=1,
            )
        ],
        human_review_points=["Confirm that the rolling proxy is scientifically acceptable."],
        risks=["Parameters are still low confidence."],
        success_criteria=["At least one candidate simulation is tied to a hypothesis."],
        next_action="human_review_framing",
    )

    payload = plan.model_dump()

    assert payload["candidate_simulations"][0]["simulation_id"] == "SIM-1"
    assert payload["milestones"][0]["review_required"] is True
    assert payload["next_action"] == "human_review_framing"
