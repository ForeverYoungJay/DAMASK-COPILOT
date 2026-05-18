from damask_copilot.agents.research_manager import ResearchManagerAgent
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.research_state import ResearchState


def test_research_manager_llm_mock_updates_state():
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "research_manager": {
                "material_system": "fcc_al",
                "objective": "Study response under uniaxial tension",
                "reasoning_summary": "The query explicitly states FCC Al under tension.",
            }
        },
    )
    state = ResearchState(user_query="Study FCC Al under uniaxial tension", use_llm=True)
    updated = ResearchManagerAgent(use_llm=True, llm_runner=runner).run(state)

    assert updated.goal is not None
    assert updated.goal.material_system == "fcc_al"
    assert updated.research_manager_output is not None
    assert updated.traces[-1].event == "goal_inferred_llm"
