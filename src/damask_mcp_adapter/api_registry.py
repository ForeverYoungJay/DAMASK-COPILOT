"""Lightweight registry for DAMASK MCP servers and adapter modules."""

from __future__ import annotations

from typing import Any


SERVER_REGISTRY: dict[str, dict[str, Any]] = {
    "core": {
        "module": "damask_copilot.mcp_servers.damask_core_server",
        "tools": [
            "check_damask_installation",
            "get_damask_version",
            "list_damask_modules",
            "inspect_damask_class",
            "inspect_damask_function",
        ],
    },
    "preprocess": {
        "module": "damask_copilot.mcp_servers.damask_preprocess_server",
        "tools": [
            "create_workspace",
            "write_yaml_file",
            "read_yaml_file",
            "validate_yaml_file",
            "create_simple_tension_load_yaml",
            "create_simple_compression_load_yaml",
            "create_material_yaml",
            "create_material_yaml_from_template",
            "create_empty_material_yaml",
            "inspect_material_yaml",
            "validate_material_yaml",
            "add_material_entry",
            "create_random_orientations",
            "convert_euler_to_quaternion",
            "convert_quaternion_to_euler",
            "create_random_seeds",
            "create_voronoi_grid",
            "inspect_grid",
            "scale_grid",
            "renumber_grid",
            "clean_grid",
        ],
    },
    "validation": {
        "module": "damask_copilot.mcp_servers.damask_validation_server",
        "tools": [
            "validate_material_yaml_structure",
            "validate_load_yaml_structure",
            "inspect_geometry_material_indices",
            "check_phase_homogenization_consistency",
            "check_orientation_format",
            "check_required_plasticity_parameters",
            "check_material_indices",
            "validate_simulation_setup",
        ],
    },
    "runner": {
        "module": "damask_copilot.mcp_servers.damask_runner_server",
        "tools": [
            "find_damask_executables",
            "run_damask_grid",
            "list_workspace_files",
            "collect_result_files",
        ],
    },
    "postprocess": {
        "module": "damask_copilot.mcp_servers.damask_postprocess_server",
        "tools": [
            "inspect_hdf5_result",
            "inspect_result_file",
            "list_result_data",
            "list_result_increments",
            "list_result_fields",
            "add_strain",
            "add_equivalent_mises",
            "add_deviator",
            "add_spherical",
            "add_gradient",
            "add_divergence",
            "add_curl",
            "extract_volume_average",
            "extract_stress_strain_curve",
            "export_result_vtk",
        ],
    },
    "misc": {
        "module": "damask_copilot.mcp_servers.damask_misc_server",
        "tools": [
            "load_table",
            "inspect_table",
            "get_table_column",
            "rename_table_column",
            "sort_table_by",
            "inspect_dream3d_base_group",
            "inspect_dream3d_cell_data_group",
            "miller_to_bravais",
            "bravais_to_miller",
            "grid_point_to_node",
            "grid_node_to_point",
            "grid_ravel",
            "grid_unravel",
            "validate_regular_grid_coordinates",
        ],
    },
    "unified": {
        "module": "damask_copilot.mcp_servers.damask_server",
        "tools": [
            "describe_damask_mcp",
        ],
    },
}


def list_registered_servers() -> dict[str, Any]:
    """Return a JSON-safe view of the current server registry."""
    return {
        "ok": True,
        "server_count": len(SERVER_REGISTRY),
        "servers": SERVER_REGISTRY,
    }
