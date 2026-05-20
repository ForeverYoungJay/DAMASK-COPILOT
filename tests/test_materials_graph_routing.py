from damask_copilot.graph.materials_research_routing import route_after_iteration_decider


def test_route_after_iteration_decider_routes_to_parameter_agent():
    state = {"iteration_decision": {"action": "revise_parameters", "continue_research": True}}

    assert route_after_iteration_decider(state) == "parameter_agent"


def test_route_after_iteration_decider_routes_to_human_review():
    state = {"iteration_decision": {"action": "request_human_input", "continue_research": True}}

    assert route_after_iteration_decider(state) == "human_review_framing"


def test_route_after_iteration_decider_routes_to_report_on_finish():
    state = {"iteration_decision": {"action": "finish", "continue_research": False}}

    assert route_after_iteration_decider(state) == "research_report"
