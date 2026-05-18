from damask_copilot.schemas.llm_outputs import (
    MaterialKnowledgeOutput,
    ResearchManagerOutput,
    ScientificCriticOutput,
    SimulationPlannerOutput,
)


def test_llm_output_schemas_validate():
    research = ResearchManagerOutput(
        material_system="fcc_al",
        objective="Study response under uniaxial tension",
        reasoning_summary="The query explicitly requests FCC Al under tension.",
    )
    knowledge = MaterialKnowledgeOutput(
        material_label="FCC Aluminum Demo",
        crystal_structure="fcc",
        knowledge_summary="Use a small uniaxial plan first.",
        planning_considerations=["Prefer a low-cost smoke test."],
    )
    planner = SimulationPlannerOutput(
        plan_name="fcc_al_smoke_test",
        summary="Small tension smoke test.",
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
    )
    critic = ScientificCriticOutput(
        summary="Preliminary critique complete.",
        strengths=["The plan is small."],
        limitations=["No result file exists yet."],
        next_steps=["Run the deterministic checker."],
    )

    assert research.material_system == "fcc_al"
    assert knowledge.crystal_structure == "fcc"
    assert planner.steps == 5
    assert planner.outputs == ["stress_strain_curve"]
    assert critic.limitations[0] == "No result file exists yet."
