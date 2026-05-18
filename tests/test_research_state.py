from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState


def test_research_state_defaults():
    state = ResearchState(user_query="Study FCC Al under uniaxial tension", dry_run=True)
    assert state.status == "initialized"
    assert state.traces == []
    assert state.goal is None


def test_research_state_accepts_nested_models():
    state = ResearchState(
        user_query="Study FCC Al under uniaxial tension",
        goal=ResearchGoal(
            user_query="Study FCC Al under uniaxial tension",
            material_system="fcc_al",
            objective="Study response under uniaxial tension",
        ),
        checker_report=CheckerReport(ok=True),
    )
    assert state.goal.material_system == "fcc_al"
    assert state.checker_report.ok is True
