from damask_copilot.agents.simulation_planner import SimulationPlannerAgent
from damask_copilot.schemas.project_plan import CandidateSimulation, ProjectMilestone, ProjectPlan
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState


def test_simulation_planner_consumes_project_plan_and_selected_candidate():
    state = ResearchState(
        user_query="Study Ni3Al L12 rolling anisotropy",
        goal=ResearchGoal(
            user_query="Study Ni3Al L12 rolling anisotropy",
            material_system="ni3al_l12",
            objective="Explain anisotropy during rolling",
        ),
        selected_material_key="ni3al_l12",
        smoke_test=True,
        project_plan=ProjectPlan(
            project_objective="Build a rolling-anisotropy research roadmap.",
            research_questions=["Can a rolling proxy explain the anisotropy trend?"],
            milestones=[
                ProjectMilestone(
                    milestone_id="M1",
                    title="Select the first simulation",
                    description="Choose the first executable DAMASK screen.",
                    deliverables=["Selected simulation brief"],
                )
            ],
            deliverables=["Roadmap"],
            candidate_simulations=[
                CandidateSimulation(
                    simulation_id="SIM-ROLL-2",
                    title="Rolling proxy screen",
                    objective="Test whether a plane-strain rolling proxy reproduces the anisotropy trend.",
                    why_needed="It is the first executable screen for the core project question.",
                    target_hypotheses=["H1"],
                    required_evidence=["Anisotropy trend"],
                    simulation_type_hint="plane_strain_rolling_proxy",
                    priority=1,
                )
            ],
            success_criteria=["A concrete executable plan exists for the selected candidate simulation."],
            next_action="simulation_planner",
        ),
        candidate_simulations=[
            CandidateSimulation(
                simulation_id="SIM-ROLL-2",
                title="Rolling proxy screen",
                objective="Test whether a plane-strain rolling proxy reproduces the anisotropy trend.",
                why_needed="It is the first executable screen for the core project question.",
                target_hypotheses=["H1"],
                required_evidence=["Anisotropy trend"],
                simulation_type_hint="plane_strain_rolling_proxy",
                priority=1,
            )
        ],
        selected_simulation_id="SIM-ROLL-2",
    )

    updated = SimulationPlannerAgent().run(state)

    assert updated.simulation_plan is not None
    assert updated.simulation_plan.name.endswith("sim_roll_2")
    assert updated.simulation_plan.loading.mode == "plane_strain_rolling_proxy"
    assert "SIM-ROLL-2" in updated.simulation_plan.summary
