from damask_copilot.agents.parameter_database import ParameterDatabaseAgent
from damask_copilot.memory.parameter_store import ParameterStore
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState


def test_fcc_al_material_database_selects_demo_card_from_alias():
    state = ResearchState(
        user_query="Study FCC aluminum under uniaxial tension",
        goal=ResearchGoal(
            user_query="Study FCC aluminum under uniaxial tension",
            material_system="FCC aluminum",
            objective="Study response under uniaxial tension",
        ),
    )

    updated = ParameterDatabaseAgent().run(state)

    assert updated.selected_material_key == "fcc_al"
    assert updated.material_card is not None
    assert updated.material_card.material_name == "FCC Aluminum Demo"
    assert updated.material_card.is_demo_template is True


def test_parameter_store_loads_multiple_demo_materials():
    store = ParameterStore()
    store.load_library()

    assert store.resolve("FCC copper") is not None
    assert store.resolve("Ni3Al L12") is not None
    assert store.resolve("aluminium").material_id == "fcc_al"
