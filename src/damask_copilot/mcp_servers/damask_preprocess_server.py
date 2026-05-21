"""Thin FastMCP server for DAMASK preprocess workflows."""

from __future__ import annotations

from damask_copilot.mcp_servers._fastmcp import FastMCP

from damask_mcp_adapter.modules.grid_tools import (
    clean_grid as clean_grid_impl,
    create_voronoi_grid as create_voronoi_grid_impl,
    inspect_grid as inspect_grid_impl,
    renumber_grid as renumber_grid_impl,
    scale_grid as scale_grid_impl,
)
from damask_mcp_adapter.modules.config_material import (
    create_material_yaml as create_material_yaml_impl,
    create_material_yaml_from_template as create_material_yaml_from_template_impl,
)
from damask_mcp_adapter.modules.loading import (
    create_simple_compression_load_yaml as create_simple_compression_load_yaml_impl,
    create_simple_tension_load_yaml as create_simple_tension_load_yaml_impl,
)
from damask_mcp_adapter.modules.material_tools import (
    add_material_entry as add_material_entry_impl,
    create_empty_material_yaml as create_empty_material_yaml_impl,
    inspect_material_yaml as inspect_material_yaml_impl,
    validate_material_yaml as validate_material_yaml_impl,
)
from damask_mcp_adapter.modules.rotation_tools import (
    convert_euler_to_quaternion as convert_euler_to_quaternion_impl,
    convert_quaternion_to_euler as convert_quaternion_to_euler_impl,
    create_random_orientations as create_random_orientations_impl,
)
from damask_mcp_adapter.modules.seed_tools import create_random_seeds as create_random_seeds_impl
from damask_mcp_adapter.modules.yaml_tools import (
    read_yaml_file as read_yaml_file_impl,
    validate_yaml_file as validate_yaml_file_impl,
    write_yaml_file as write_yaml_file_impl,
)
from damask_mcp_adapter.validators import resolve_workspace_dir

mcp = FastMCP("damask-preprocess")


@mcp.tool()
def write_yaml_file(path: str, data: object) -> dict:
    """Write a YAML mapping under workspaces/."""
    return write_yaml_file_impl(path=path, data=data)


@mcp.tool()
def create_workspace(name: str) -> dict:
    """Create or reuse a workspace under workspaces/."""
    workspace_path = resolve_workspace_dir(name)
    workspace_path.mkdir(parents=True, exist_ok=True)
    (workspace_path / "results").mkdir(parents=True, exist_ok=True)
    return {
        "ok": True,
        "name": name,
        "path": str(workspace_path.resolve()),
    }


@mcp.tool()
def read_yaml_file(path: str) -> dict:
    """Read a YAML file and return its parsed mapping."""
    return read_yaml_file_impl(path)


@mcp.tool()
def validate_yaml_file(path: str) -> dict:
    """Validate that a YAML file can be parsed as a mapping."""
    return validate_yaml_file_impl(path)


@mcp.tool()
def create_simple_tension_load_yaml(path: str, strain_rate: float, final_strain: float, steps: int) -> dict:
    """Create a simple uniaxial tension grid-solver load case."""
    return create_simple_tension_load_yaml_impl(path, strain_rate, final_strain, steps)


@mcp.tool()
def create_simple_compression_load_yaml(path: str, strain_rate: float, final_strain: float, steps: int) -> dict:
    """Create a simple uniaxial compression grid-solver load case."""
    return create_simple_compression_load_yaml_impl(path, strain_rate, final_strain, steps)


@mcp.tool()
def create_material_yaml(
    path: str,
    material_name: str,
    phase_name: str,
    lattice: str,
    elastic: dict,
    plastic: dict | None = None,
) -> dict:
    """Create a basic DAMASK material.yaml with one phase and one constituent."""
    return create_material_yaml_impl(path, material_name, phase_name, lattice, elastic, plastic)


@mcp.tool()
def create_material_yaml_from_template(
    path: str,
    homogenization: dict,
    phase: dict,
    material: list[dict],
) -> dict:
    """Create a DAMASK material.yaml from explicit homogenization, phase, and material mappings."""
    return create_material_yaml_from_template_impl(path, homogenization, phase, material)


@mcp.tool()
def create_empty_material_yaml(path: str) -> dict:
    """Create an empty DAMASK material.yaml skeleton under workspaces/."""
    return create_empty_material_yaml_impl(path)


@mcp.tool()
def inspect_material_yaml(path: str) -> dict:
    """Inspect a DAMASK material.yaml file."""
    return inspect_material_yaml_impl(path)


@mcp.tool()
def validate_material_yaml(path: str) -> dict:
    """Validate a DAMASK material.yaml file with DAMASK's own checks."""
    return validate_material_yaml_impl(path)


@mcp.tool()
def add_material_entry(
    path: str,
    homogenization: str,
    phase: str,
    orientation_quaternion: list[float],
    volume_fraction: float = 1.0,
) -> dict:
    """Add one material entry to an existing DAMASK material.yaml under workspaces/."""
    return add_material_entry_impl(path, homogenization, phase, orientation_quaternion, volume_fraction)


@mcp.tool()
def create_random_orientations(count: int, seed: int = 0) -> dict:
    """Create random DAMASK orientations and return quaternion summaries."""
    return create_random_orientations_impl(count, seed)


@mcp.tool()
def convert_euler_to_quaternion(euler: list[float], degrees: bool = True) -> dict:
    """Convert Bunge Euler angles to a DAMASK quaternion."""
    return convert_euler_to_quaternion_impl(euler, degrees)


@mcp.tool()
def convert_quaternion_to_euler(quaternion: list[float], degrees: bool = True) -> dict:
    """Convert a DAMASK quaternion to Bunge Euler angles."""
    return convert_quaternion_to_euler_impl(quaternion, degrees)


@mcp.tool()
def create_random_seeds(count: int, size: list[float], seed: int = 0) -> dict:
    """Create random seed points for tessellation."""
    return create_random_seeds_impl(count, size, seed)


@mcp.tool()
def create_voronoi_grid(path: str, cells: list[int], size: list[float], grains: int, seed: int = 0) -> dict:
    """Create a Voronoi tessellation grid and save it as .vti under workspaces/."""
    return create_voronoi_grid_impl(path, cells, size, grains, seed)


@mcp.tool()
def inspect_grid(path: str) -> dict:
    """Inspect a DAMASK VTI grid file."""
    return inspect_grid_impl(path)


@mcp.tool()
def scale_grid(path: str, cells: list[int]) -> dict:
    """Scale a DAMASK grid to new cell counts and overwrite the workspace file."""
    return scale_grid_impl(path, cells)


@mcp.tool()
def renumber_grid(path: str) -> dict:
    """Renumber material IDs in a DAMASK grid and overwrite the workspace file."""
    return renumber_grid_impl(path)


@mcp.tool()
def clean_grid(
    path: str,
    distance: float = 1.7320508075688772,
    selection: list[int] | None = None,
    invert_selection: bool = False,
    periodic: bool = True,
    seed: int = 0,
) -> dict:
    """Smooth a DAMASK grid with GeomGrid.clean and overwrite the workspace file."""
    return clean_grid_impl(path, distance, selection, invert_selection, periodic, seed)


if __name__ == "__main__":
    mcp.run()
