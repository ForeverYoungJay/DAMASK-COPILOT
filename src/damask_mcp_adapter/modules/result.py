"""Compatibility wrappers for result post-processing helpers."""

from __future__ import annotations

from typing import Any

from damask_mcp_adapter.modules import result_tools
from damask_mcp_adapter.workspace import import_damask


def _forward(function_name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    result_tools.import_damask = import_damask
    function = getattr(result_tools, function_name)
    return function(*args, **kwargs)


def inspect_hdf5_result(path: str, max_items: int = 200) -> dict[str, Any]:
    return _forward("inspect_hdf5_result", path, max_items=max_items)


def inspect_result_file(path: str) -> dict[str, Any]:
    return _forward("inspect_result_file", path)


def list_result_data(path: str) -> dict[str, Any]:
    return _forward("list_result_data", path)


def list_result_fields(path: str) -> dict[str, Any]:
    return _forward("list_result_fields", path)


def list_result_increments(path: str) -> dict[str, Any]:
    return _forward("list_result_increments", path)


def add_strain(path: str, F: str = "F", t: str = "V", m: float = 0.0) -> dict[str, Any]:
    return _forward("add_strain", path, F=F, t=t, m=m)


def add_equivalent_mises(path: str, T_sym: str, kind: str | None = None) -> dict[str, Any]:
    return _forward("add_equivalent_mises", path, T_sym=T_sym, kind=kind)


def add_deviator(path: str, T: str) -> dict[str, Any]:
    return _forward("add_deviator", path, T=T)


def add_spherical(path: str, T: str) -> dict[str, Any]:
    return _forward("add_spherical", path, T=T)


def add_gradient(path: str, f: str) -> dict[str, Any]:
    return _forward("add_gradient", path, f=f)


def add_divergence(path: str, f: str) -> dict[str, Any]:
    return _forward("add_divergence", path, f=f)


def add_curl(path: str, f: str) -> dict[str, Any]:
    return _forward("add_curl", path, f=f)


def extract_volume_average(path: str, field: str, output_csv: str | None = None) -> dict[str, Any]:
    return _forward("extract_volume_average", path, field=field, output_csv=output_csv)


def extract_stress_strain_curve(path: str, output_csv: str) -> dict[str, Any]:
    return _forward("extract_stress_strain_curve", path, output_csv=output_csv)


def export_result_vtk(path: str, output_dir: str) -> dict[str, Any]:
    return _forward("export_result_vtk", path, output_dir=output_dir)

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
    "import_damask",
]
