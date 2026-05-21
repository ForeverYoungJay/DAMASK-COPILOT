from damask_copilot.graph.materials_research_graph import build_materials_research_graph
from damask_copilot.graph.materials_research_nodes import build_v1_materials_research_nodes


def test_graph_includes_v1_project_planner_node_and_edges():
    nodes = build_v1_materials_research_nodes()
    assert "project_planner" in nodes

    app = build_materials_research_graph(checkpoint=False)
    graph = app.get_graph()
    node_names = set(getattr(graph, "nodes", {}).keys())
    edge_pairs = {
        (getattr(edge, "source", None), getattr(edge, "target", None))
        for edge in getattr(graph, "edges", [])
    }

    assert "project_planner" in node_names
    assert ("scientific_knowledge", "project_planner") in edge_pairs
    assert ("project_planner", "simulation_designer") in edge_pairs
