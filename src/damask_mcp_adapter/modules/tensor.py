"""Safe wrappers for selected DAMASK tensor functions."""

from __future__ import annotations

from typing import Any

import numpy as np

from damask_mcp_adapter.serializers import summarize_array
from damask_mcp_adapter.workspace import import_damask


def compute_deviatoric(T: list[list[float]] | list[list[list[float]]]) -> dict[str, Any]:
    """Compute the deviatoric part of a tensor using damask.tensor.deviatoric."""
    damask = import_damask()
    tensor = np.asarray(T, dtype=float)
    result = damask.tensor.deviatoric(tensor)
    return {"ok": True, "input_shape": list(tensor.shape), "summary": summarize_array(result)}


def compute_spherical(T: list[list[float]] | list[list[list[float]]], tensor: bool = True) -> dict[str, Any]:
    """Compute the spherical part of a tensor using damask.tensor.spherical."""
    damask = import_damask()
    data = np.asarray(T, dtype=float)
    result = damask.tensor.spherical(data, tensor=tensor)
    return {"ok": True, "input_shape": list(data.shape), "tensor": tensor, "summary": summarize_array(result)}


__all__ = ["compute_deviatoric", "compute_spherical"]
