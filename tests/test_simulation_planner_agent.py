from damask_copilot.agents.simulation_planner import SimulationPlannerAgent
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState


def test_simulation_planner_creates_small_tension_smoke_test():
    state = ResearchState(
        user_query="Study FCC Al under uniaxial tension",
        goal=ResearchGoal(
            user_query="Study FCC Al under uniaxial tension",
            material_system="fcc_al",
            objective="Study response under uniaxial tension",
        ),
        selected_material_key="fcc_al",
    )

    updated = SimulationPlannerAgent().run(state)

    assert updated.simulation_plan is not None
    assert updated.simulation_plan.loading.mode == "uniaxial_tension"
    assert updated.simulation_plan.loading.steps == 5
    assert updated.simulation_plan.geometry.cells == [8, 8, 8]
