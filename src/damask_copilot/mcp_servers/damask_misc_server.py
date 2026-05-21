"""Thin FastMCP server for DAMASK miscellaneous workflows."""

from __future__ import annotations

from damask_copilot.mcp_servers._fastmcp import FastMCP

from damask_mcp_adapter.modules.grid_filter_tools import (
    grid_node_to_point as grid_node_to_point_impl,
    grid_point_to_node as grid_point_to_node_impl,
    grid_ravel as grid_ravel_impl,
    grid_unravel as grid_unravel_impl,
    validate_regular_grid_coordinates as validate_regular_grid_coordinates_impl,
)
from damask_mcp_adapter.modules.table_tools import (
    get_table_column as get_table_column_impl,
    inspect_table as inspect_table_impl,
    load_table as load_table_impl,
    rename_table_column as rename_table_column_impl,
    sort_table_by as sort_table_by_impl,
)
from damask_mcp_adapter.modules.util_tools import (
    bravais_to_miller as bravais_to_miller_impl,
    inspect_dream3d_base_group as inspect_dream3d_base_group_impl,
    inspect_dream3d_cell_data_group as inspect_dream3d_cell_data_group_impl,
    miller_to_bravais as miller_to_bravais_impl,
)

mcp = FastMCP("damask-misc")


@mcp.tool()
def load_table(path: str) -> dict:
    """Load a DAMASK table and return a compact summary."""
    return load_table_impl(path)


@mcp.tool()
def inspect_table(path: str) -> dict:
    """Inspect a DAMASK table file."""
    return inspect_table_impl(path)


@mcp.tool()
def get_table_column(path: str, label: str, output_npy: str | None = None) -> dict:
    """Get one DAMASK table column as a compact summary."""
    return get_table_column_impl(path, label, output_npy)


@mcp.tool()
def rename_table_column(path: str, old: str, new: str, output_path: str | None = None) -> dict:
    """Rename a DAMASK table column and save under workspaces/."""
    return rename_table_column_impl(path, old, new, output_path)


@mcp.tool()
def sort_table_by(path: str, labels: str | list[str], ascending: bool = True, output_path: str | None = None) -> dict:
    """Sort a DAMASK table by one or more columns and save under workspaces/."""
    return sort_table_by_impl(path, labels, ascending, output_path)


@mcp.tool()
def inspect_dream3d_base_group(path: str) -> dict:
    """Inspect the detected DREAM3D base group."""
    return inspect_dream3d_base_group_impl(path)


@mcp.tool()
def inspect_dream3d_cell_data_group(path: str) -> dict:
    """Inspect the detected DREAM3D cell-data group."""
    return inspect_dream3d_cell_data_group_impl(path)


@mcp.tool()
def miller_to_bravais(uvw: list[int] | None = None, hkl: list[int] | None = None) -> dict:
    """Convert 3-index Miller direction or plane indices to 4-index Miller-Bravais indices."""
    return miller_to_bravais_impl(uvw, hkl)


@mcp.tool()
def bravais_to_miller(uvtw: list[int] | None = None, hkil: list[int] | None = None) -> dict:
    """Convert 4-index Miller-Bravais direction or plane indices to 3-index Miller indices."""
    return bravais_to_miller_impl(uvtw, hkil)


@mcp.tool()
def grid_point_to_node(cell_data: list, output_npy: str | None = None) -> dict:
    """Interpolate periodic point data to nodal data."""
    return grid_point_to_node_impl(cell_data, output_npy)


@mcp.tool()
def grid_node_to_point(node_data: list, output_npy: str | None = None) -> dict:
    """Interpolate periodic nodal data to point data."""
    return grid_node_to_point_impl(node_data, output_npy)


@mcp.tool()
def grid_ravel(data: list, flatten: bool = False, output_npy: str | None = None) -> dict:
    """Convert unraveled 3D regular-grid data to raveled representation."""
    return grid_ravel_impl(data, flatten, output_npy)


@mcp.tool()
def grid_unravel(data: list, cells: list[int], flatten: bool = False, output_npy: str | None = None) -> dict:
    """Convert raveled regular-grid data to unraveled representation."""
    return grid_unravel_impl(data, cells, flatten, output_npy)


@mcp.tool()
def validate_regular_grid_coordinates(coordinates0: list[list[float]]) -> dict:
    """Check whether coordinates form a regular ordered grid."""
    return validate_regular_grid_coordinates_impl(coordinates0)


if __name__ == "__main__":
    mcp.run()
