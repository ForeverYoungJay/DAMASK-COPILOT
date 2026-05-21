from damask_copilot.graph.state import ResearchState as WorkflowResearchState
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


def test_v1_research_state_initializes_with_user_goal():
    state = WorkflowResearchState(user_goal="Calibrate Ni3Al DAMASK model")
    assert state.user_goal == "Calibrate Ni3Al DAMASK model"


def test_v1_research_state_defaults_iteration_to_zero():
    state = WorkflowResearchState(user_goal="Run a DAMASK smoke test")
    assert state.iteration == 0


def test_v1_research_state_has_safe_default_max_iterations():
    state = WorkflowResearchState(user_goal="Run a DAMASK smoke test")
    assert state.max_iterations == 3
