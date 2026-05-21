"""Thin FastMCP server for DAMASK postprocess workflows."""

from __future__ import annotations

from damask_copilot.mcp_servers._fastmcp import FastMCP

from damask_mcp_adapter.modules.result_tools import (
    add_curl as add_curl_impl,
    add_deviator as add_deviator_impl,
    add_divergence as add_divergence_impl,
    add_equivalent_mises as add_equivalent_mises_impl,
    add_gradient as add_gradient_impl,
    add_spherical as add_spherical_impl,
    add_strain as add_strain_impl,
    export_result_vtk as export_result_vtk_impl,
    extract_stress_strain_curve as extract_stress_strain_curve_impl,
    extract_volume_average as extract_volume_average_impl,
    inspect_hdf5_result as inspect_hdf5_result_impl,
    inspect_result_file as inspect_result_file_impl,
    list_result_data as list_result_data_impl,
    list_result_fields as list_result_fields_impl,
    list_result_increments as list_result_increments_impl,
)

mcp = FastMCP("damask-postprocess")


@mcp.tool()
def inspect_hdf5_result(path: str, max_items: int = 200) -> dict:
    """Inspect an HDF5 file structure without loading large datasets."""
    return inspect_hdf5_result_impl(path=path, max_items=max_items)


@mcp.tool()
def inspect_result_file(path: str) -> dict:
    """Inspect a DAMASK result file through damask.Result."""
    return inspect_result_file_impl(path)


@mcp.tool()
def list_result_data(path: str) -> dict:
    """List active datasets in a DAMASK result file."""
    return list_result_data_impl(path)


@mcp.tool()
def list_result_increments(path: str) -> dict:
    """List visible increments in a DAMASK result file."""
    return list_result_increments_impl(path)


@mcp.tool()
def list_result_fields(path: str) -> dict:
    """List visible result fields in a DAMASK result file."""
    return list_result_fields_impl(path)


@mcp.tool()
def add_strain(path: str, F: str = "F", t: str = "V", m: float = 0.0) -> dict:
    """Add strain data to a DAMASK result file in-place."""
    return add_strain_impl(path, F, t, m)


@mcp.tool()
def add_equivalent_mises(path: str, T_sym: str, kind: str | None = None) -> dict:
    """Add von Mises equivalent data to a DAMASK result file in-place."""
    return add_equivalent_mises_impl(path, T_sym, kind)


@mcp.tool()
def add_deviator(path: str, T: str) -> dict:
    """Add tensor deviator data to a DAMASK result file in-place."""
    return add_deviator_impl(path, T)


@mcp.tool()
def add_spherical(path: str, T: str) -> dict:
    """Add tensor spherical data to a DAMASK result file in-place."""
    return add_spherical_impl(path, T)


@mcp.tool()
def add_gradient(path: str, f: str) -> dict:
    """Add gradient data to a DAMASK result file in-place."""
    return add_gradient_impl(path, f)


@mcp.tool()
def add_divergence(path: str, f: str) -> dict:
    """Add divergence data to a DAMASK result file in-place."""
    return add_divergence_impl(path, f)


@mcp.tool()
def add_curl(path: str, f: str) -> dict:
    """Add curl data to a DAMASK result file in-place."""
    return add_curl_impl(path, f)


@mcp.tool()
def extract_volume_average(path: str, field: str, output_csv: str | None = None) -> dict:
    """Extract per-increment volume averages for a result field."""
    return extract_volume_average_impl(path, field, output_csv)


@mcp.tool()
def extract_stress_strain_curve(path: str, output_csv: str) -> dict:
    """Extract a simple stress-strain curve from averaged F and P."""
    return extract_stress_strain_curve_impl(path, output_csv)


@mcp.tool()
def export_result_vtk(path: str, output_dir: str) -> dict:
    """Export a DAMASK result file to VTK files under workspaces/."""
    return export_result_vtk_impl(path, output_dir)


if __name__ == "__main__":
    mcp.run()
