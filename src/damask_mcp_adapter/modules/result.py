"""Compatibility wrappers for result post-processing helpers."""

from __future__ import annotations

from damask_mcp_adapter.modules.result_tools import (
    add_curl,
    add_deviator,
    add_divergence,
    add_equivalent_mises,
    add_gradient,
    add_spherical,
    add_strain,
    export_result_vtk,
    extract_stress_strain_curve,
    extract_volume_average,
    inspect_hdf5_result,
    inspect_result_file,
    list_result_data,
    list_result_fields,
    list_result_increments,
)

__all__ = [
    "add_curl",
    "add_deviator",
    "add_divergence",
    "add_equivalent_mises",
    "add_gradient",
    "add_spherical",
    "add_strain",
    "export_result_vtk",
    "extract_stress_strain_curve",
    "extract_volume_average",
    "inspect_hdf5_result",
    "inspect_result_file",
    "list_result_data",
    "list_result_fields",
    "list_result_increments",
]
