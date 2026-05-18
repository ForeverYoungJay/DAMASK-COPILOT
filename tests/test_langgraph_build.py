from damask_copilot.graph.graph import build_damask_research_graph


def test_langgraph_build_returns_compiled_graph():
    app = build_damask_research_graph(checkpoint=False)

    assert app is not None
    assert hasattr(app, "invoke")
    assert hasattr(app, "stream")
