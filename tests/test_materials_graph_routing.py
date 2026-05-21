from damask_copilot.graph.routing import route_after_analysis_action


class _State:
    def __init__(self, next_action):
        self.next_action = next_action


def test_route_after_analysis_routes_to_simulation_designer_for_parameter_update():
    state = _State({"type": "update_parameters"})
    assert route_after_analysis_action(state) == "simulation_designer"


def test_route_after_analysis_routes_to_report_for_human_review():
    state = _State({"type": "request_human_review"})
    assert route_after_analysis_action(state) == "research_report"


def test_route_after_analysis_routes_to_report_on_stop():
    state = _State({"type": "stop"})
    assert route_after_analysis_action(state) == "research_report"
