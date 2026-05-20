from damask_copilot.graph.materials_research_graph import build_materials_research_graph
from damask_copilot.graph.materials_research_nodes import build_materials_research_nodes


def test_graph_includes_project_planner_node_and_edges():
    nodes = build_materials_research_nodes()
    assert "research_project_planner" in nodes

    app = build_materials_research_graph(checkpoint=False)
    graph = app.get_graph()
    node_names = set(getattr(graph, "nodes", {}).keys())
    edge_pairs = {
        (getattr(edge, "source", None), getattr(edge, "target", None))
        for edge in getattr(graph, "edges", [])
    }

    assert "research_project_planner" in node_names
    assert ("parameter_agent", "research_project_planner") in edge_pairs
    assert ("research_project_planner", "human_review_framing") in edge_pairs
