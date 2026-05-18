from damask_copilot.agents.simulation_planner import SimulationPlannerAgent
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState


def test_simulation_planner_llm_mock_updates_state():
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "simulation_planner": {
                "plan_name": "fcc_al_smoke_test",
                "summary": "Small tension smoke test.",
                "grid_type": "voronoi",
                "cells": [8, 8, 8],
                "size": [1.0, 1.0, 1.0],
                "grains": 8,
                "loading_mode": "uniaxial_tension",
                "loading_direction": "x",
                "final_strain": 0.02,
                "strain_rate": 1.0e-3,
                "steps": 5,
            }
        },
    )
    state = ResearchState(
        user_query="Study FCC Al under uniaxial tension",
        use_llm=True,
        dry_run=True,
        smoke_test=True,
        goal=ResearchGoal(
            user_query="Study FCC Al under uniaxial tension",
            material_system="fcc_al",
            objective="Study response under uniaxial tension",
        ),
        selected_material_key="fcc_al",
    )

    updated = SimulationPlannerAgent(use_llm=True, llm_runner=runner).run(state)

    assert updated.simulation_plan is not None
    assert updated.simulation_planner_output is not None
    assert updated.simulation_plan.loading.mode == "uniaxial_tension"
    assert updated.traces[-1].event == "plan_created_llm"
