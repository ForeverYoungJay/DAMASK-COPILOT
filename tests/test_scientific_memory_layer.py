from damask_copilot.graph.state import ResearchState
from damask_copilot.memory.scientific_memory import ScientificMemoryLayer


def test_scientific_memory_layer_collects_expected_domains(tmp_path):
    memory = ScientificMemoryLayer(workspace_root=tmp_path / "workspaces")

    state = ResearchState(
        user_goal="Calibrate Ni3Al crystal plasticity parameters.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        experimental_data={"curve": {"strain": [0.0, 0.01], "stress": [0.0, 100.0]}},
        simulation_spec={"parameter_values": {"n_sl": 25.0}},
        run_result={"status": "failed", "failure_category": "model", "error": "material index out of bounds"},
        postprocessing_result={"status": "not_available"},
        alignment_result={"status": "comparison_not_possible"},
        next_action={"type": "change_model", "reason": "Repair the material mapping."},
        parameter_history=[{"iteration": 0, "parameters": {"n_sl": 25.0}}],
    )

    memory.remember_state(state)
    context = memory.collect_context(material_system="ni3al_l12", workflow_type="calibration")

    assert "literature_memory" in context
    assert "cp_parameter_database" in context
    assert "damask_input_templates" in context
    assert "simulation_result_database" in context
    assert "experimental_data_database" in context
    assert "optimization_history" in context
    assert "error_fix_database" in context
    assert "materials_knowledge_graph" in context
    assert context["cp_parameter_database"]["material_id"] == "ni3al_l12"
    assert context["error_fix_database"][0]["failure_category"] == "model"


def test_scientific_memory_knowledge_graph_contains_material_phase_links(tmp_path):
    memory = ScientificMemoryLayer(workspace_root=tmp_path / "workspaces")
    graph = memory.collect_context(material_system="ni3al_l12")["materials_knowledge_graph"]

    edge_types = {edge["type"] for edge in graph["edges"]}
    assert graph["material"] == "ni3al_l12"
    assert "has_phase" in edge_types
    assert "has_crystal_structure" in edge_types
