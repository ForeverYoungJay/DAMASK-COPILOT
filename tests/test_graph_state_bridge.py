from damask_copilot.graph.state import create_initial_state, graph_state_from_legacy, legacy_state_from_graph
from damask_copilot.schemas.llm_outputs import ResearchManagerOutput, ScientificCriticOutput, SimulationPlannerOutput
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


def test_graph_state_bridge_preserves_selected_material_and_outputs():
    graph_state = create_initial_state(
        user_query="Study FCC aluminum under uniaxial tension",
        mode="dry_run",
        use_llm=True,
        model="gpt-5.5",
        max_iterations=1,
    )
    legacy = ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        dry_run=True,
        use_llm=True,
        model_name="gpt-5.5",
        selected_material_key="fcc_al",
        goal=ResearchGoal(
            user_query="Study FCC aluminum under uniaxial tension",
            material_system="fcc_al",
            objective="Study response under uniaxial tension",
        ),
        research_manager_output=ResearchManagerOutput(
            material_system="fcc_al",
            objective="Study response under uniaxial tension",
            reasoning_summary="Mock reasoning.",
        ),
        simulation_plan=SimulationPlan(
            name="fcc_al_smoke_test",
            summary="Small smoke test.",
            workspace="fcc_al_smoke_test",
            material_id="fcc_al",
            outputs=["stress_strain_curve"],
            geometry=GeometrySpec(grid_type="voronoi", cells=[8, 8, 8], size=[1.0, 1.0, 1.0], grains=8),
            loading=LoadingSpec(mode="uniaxial_tension", direction="x", final_strain=0.02, strain_rate=1.0e-3, steps=5),
        ),
        simulation_planner_output=SimulationPlannerOutput(
            plan_name="fcc_al_smoke_test",
            summary="Small smoke test.",
            grid_type="voronoi",
            cells=[8, 8, 8],
            size=[1.0, 1.0, 1.0],
            grains=8,
            loading_mode="uniaxial_tension",
            loading_direction="x",
            final_strain=0.02,
            strain_rate=1.0e-3,
            steps=5,
            outputs=["stress_strain_curve"],
        ),
        scientific_critic_output=ScientificCriticOutput(
            summary="Preliminary critique.",
            strengths=["Conservative setup."],
            limitations=["No numerical results."],
            next_steps=["Run a smoke test."],
        ),
    )

    merged = graph_state_from_legacy(graph_state, legacy)
    round_tripped = legacy_state_from_graph(merged)

    assert merged["selected_material_key"] == "fcc_al"
    assert merged["research_manager_output"] is not None
    assert merged["simulation_planner_output"] is not None
    assert merged["scientific_critic_output"] is not None
    assert round_tripped.selected_material_key == "fcc_al"
    assert round_tripped.research_manager_output is not None
    assert round_tripped.simulation_planner_output is not None
