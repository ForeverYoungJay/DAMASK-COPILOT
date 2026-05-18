"""Regular-grid filter tools mapped from DAMASK miscellaneous docs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from damask_mcp_adapter.serializers import summarize_array
from damask_mcp_adapter.validators import ensure_workspace_write_path
from damask_mcp_adapter.workspace import import_damask


def _save_optional(array: np.ndarray, output_npy: str | None) -> str | None:
    if output_npy is None:
        return None
    output_path = ensure_workspace_write_path(output_npy)
    np.save(output_path, array)
    return str(output_path)


def grid_point_to_node(cell_data: list, output_npy: str | None = None) -> dict[str, Any]:
    """Interpolate periodic point data to nodal data."""
    damask = import_damask()
    array = np.asarray(cell_data)
    converted = damask.grid_filters.point_to_node(array)
    return {
        "ok": True,
        "summary": summarize_array(converted),
        "output_npy": _save_optional(converted, output_npy),
    }


def grid_node_to_point(node_data: list, output_npy: str | None = None) -> dict[str, Any]:
    """Interpolate periodic nodal data to point data."""
    damask = import_damask()
    array = np.asarray(node_data)
    converted = damask.grid_filters.node_to_point(array)
    return {
        "ok": True,
        "summary": summarize_array(converted),
        "output_npy": _save_optional(converted, output_npy),
    }


def grid_ravel(data: list, flatten: bool = False, output_npy: str | None = None) -> dict[str, Any]:
    """Convert unraveled 3D regular-grid data to raveled representation."""
    damask = import_damask()
    array = np.asarray(data)
    converted = damask.grid_filters.ravel(array, flatten=flatten)
    return {
        "ok": True,
        "summary": summarize_array(converted),
        "output_npy": _save_optional(converted, output_npy),
    }


def grid_unravel(data: list, cells: list[int], flatten: bool = False, output_npy: str | None = None) -> dict[str, Any]:
    """Convert raveled regular-grid data to unraveled representation."""
    damask = import_damask()
    array = np.asarray(data)
    converted = damask.grid_filters.unravel(array, cells, flatten=flatten)
    return {
        "ok": True,
        "summary": summarize_array(converted),
        "output_npy": _save_optional(converted, output_npy),
    }


def validate_regular_grid_coordinates(coordinates0: list[list[float]]) -> dict[str, Any]:
    """Check whether coordinates form a regular ordered grid."""
    damask = import_damask()
    array = np.asarray(coordinates0, dtype=float)
    is_valid = bool(damask.grid_filters.coordinates0_valid(array))
    return {
        "ok": True,
        "valid": is_valid,
        "summary": summarize_array(array),
    }


__all__ = [
    "grid_node_to_point",
    "grid_point_to_node",
    "grid_ravel",
    "grid_unravel",
    "validate_regular_grid_coordinates",
]
