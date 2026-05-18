import pytest

from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import ResearchManagerOutput


def test_structured_llm_runner_mock_returns_parsed_model():
    runner = StructuredLLMRunner(
        mock_mode=True,
        mock_outputs={
            "research_manager": {
                "material_system": "fcc_al",
                "objective": "Study response under uniaxial tension",
                "reasoning_summary": "The query names FCC Al and tension.",
            }
        },
    )
    parsed = runner.run_structured(
        prompt_name="research_manager",
        system_prompt="system",
        user_prompt="user",
        output_schema=ResearchManagerOutput,
    )
    assert parsed.material_system == "fcc_al"


def test_structured_llm_runner_mock_raises_on_parse_failure():
    runner = StructuredLLMRunner(mock_mode=True, mock_outputs={"research_manager": {"bad": "payload"}})
    with pytest.raises(ValueError):
        runner.run_structured(
            prompt_name="research_manager",
            system_prompt="system",
            user_prompt="user",
            output_schema=ResearchManagerOutput,
        )
