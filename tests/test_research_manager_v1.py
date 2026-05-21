from damask_copilot.agents.research_manager import ResearchManagerAgent
from damask_copilot.graph.state import ResearchState


def test_research_manager_v1_classifies_calibration_workflow():
    state = ResearchState(
        user_goal="Calibrate a DAMASK crystal plasticity model for Ni3Al using tensile stress-strain data.",
        use_llm=False,
    )

    updated = ResearchManagerAgent(use_llm=False).run(state)

    assert updated.workflow_type == "calibration"
    assert updated.material_system == "ni3al_l12"
    assert updated.needs_literature is True
    assert updated.needs_experimental_data is True
    assert updated.needs_damask_simulation is True
    assert updated.needs_parameter_optimization is True
    assert updated.needs_report is True
    assert updated.research_manager_output is not None
