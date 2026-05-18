"""Direct-call smoke test for DAMASK Copilot tool functions."""

from __future__ import annotations

import json
from pathlib import Path
import sys

def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    src_dir = project_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from damask_mcp_adapter.modules.grid_tools import clean_grid, create_voronoi_grid, inspect_grid, renumber_grid, scale_grid
    from damask_mcp_adapter.modules.grid_filter_tools import validate_regular_grid_coordinates
    from damask_mcp_adapter.modules.material_tools import (
        add_material_entry,
        create_empty_material_yaml,
        inspect_material_yaml,
        validate_material_yaml,
    )
    from damask_mcp_adapter.modules.result_tools import (
        inspect_hdf5_result,
        inspect_result_file,
        list_result_data,
        list_result_fields,
        list_result_increments,
    )
    from damask_mcp_adapter.modules.rotation_tools import (
        convert_euler_to_quaternion,
        convert_quaternion_to_euler,
        create_random_orientations,
    )
    from damask_mcp_adapter.modules.seed_tools import create_random_seeds
    from damask_mcp_adapter.modules.table_tools import inspect_table
    from damask_mcp_adapter.modules.util_tools import bravais_to_miller, miller_to_bravais
    from damask_mcp_adapter.modules.yaml_tools import read_yaml_file, validate_yaml_file, write_yaml_file
    from damask_mcp_adapter.workspace import ensure_damask_python_on_path

    ensure_damask_python_on_path()
    import damask  # noqa: F401

    workspace_dir = project_root / "workspaces" / "demo_tension"
    results_dir = workspace_dir / "results"
    sample_yaml = workspace_dir / "sample.yaml"
    material_yaml = workspace_dir / "material.yaml"
    tension_yaml = workspace_dir / "load.yaml"
    grid_path = workspace_dir / "geometry.vti"
    table_path = workspace_dir / "sample_table.txt"
    results_dir.mkdir(parents=True, exist_ok=True)
    if not table_path.exists():
        table_path.write_text("# sample\ncol\n1\n2\n", encoding="utf-8")

    results = {
        "write_yaml_file": write_yaml_file(
            path=str(sample_yaml),
            data={"example": True, "values": [1, 2, 3]},
        ),
        "read_yaml_file": read_yaml_file(str(sample_yaml)),
        "validate_yaml_file": validate_yaml_file(str(sample_yaml)),
        "create_empty_material_yaml": create_empty_material_yaml(path=str(material_yaml)),
        "add_material_entry": add_material_entry(
            path=str(material_yaml),
            homogenization="SX",
            phase="PlaceholderPhase",
            orientation_quaternion=[1.0, 0.0, 0.0, 0.0],
            volume_fraction=1.0,
        ),
        "inspect_material_yaml": inspect_material_yaml(str(material_yaml)),
        "validate_material_yaml": validate_material_yaml(str(material_yaml)),
        "create_random_orientations": create_random_orientations(4, 0),
        "convert_euler_to_quaternion": convert_euler_to_quaternion([0.0, 0.0, 0.0], True),
        "convert_quaternion_to_euler": convert_quaternion_to_euler([1.0, 0.0, 0.0, 0.0], True),
        "create_random_seeds": create_random_seeds(5, [1.0, 1.0, 1.0], 0),
        "create_voronoi_grid": create_voronoi_grid(str(grid_path), [8, 8, 8], [1.0, 1.0, 1.0], 5, 0),
        "inspect_grid": inspect_grid(str(grid_path)),
        "scale_grid": scale_grid(str(grid_path), [8, 8, 8]),
        "renumber_grid": renumber_grid(str(grid_path)),
        "clean_grid": clean_grid(str(grid_path)),
        "validate_regular_grid_coordinates": validate_regular_grid_coordinates([[0.0, 0.0, 0.0]]),
        "inspect_table": inspect_table(str(table_path)),
        "miller_to_bravais": miller_to_bravais(uvw=[1, 0, 0]),
        "bravais_to_miller": bravais_to_miller(uvtw=[1, 0, -1, 0]),
        "inspect_result_file_missing_example": inspect_result_file(str(results_dir / "missing_example.hdf5")),
        "list_result_data_missing_example": list_result_data(str(results_dir / "missing_example.hdf5")),
        "list_result_increments_missing_example": list_result_increments(str(results_dir / "missing_example.hdf5")),
        "list_result_fields_missing_example": list_result_fields(str(results_dir / "missing_example.hdf5")),
        "inspect_hdf5_result_missing_example": inspect_hdf5_result(
            path=str(results_dir / "missing_example.hdf5"),
            max_items=10,
        ),
    }

    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
