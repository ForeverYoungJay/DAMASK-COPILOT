from damask_copilot.graph.materials_research_routing import route_after_iteration_decider


def test_route_after_iteration_decider_routes_to_project_planner():
    state = {"iteration_decision": {"action": "revise_project_plan", "continue_research": True}}

    assert route_after_iteration_decider(state) == "research_project_planner"
