"""Safe wrappers for selected DAMASK mechanics functions."""

from __future__ import annotations

from typing import Any

import numpy as np

from damask_mcp_adapter.serializers import summarize_array
from damask_mcp_adapter.workspace import import_damask


def compute_strain(F: list[list[float]] | list[list[list[float]]], t: str = "V", m: float = 0.0) -> dict[str, Any]:
    """Compute strain from deformation gradients using damask.mechanics.strain."""
    damask = import_damask()
    tensor = np.asarray(F, dtype=float)
    result = damask.mechanics.strain(tensor, t, m)
    return {"ok": True, "input_shape": list(tensor.shape), "summary": summarize_array(result)}


def compute_cauchy_stress(P: list[list[float]] | list[list[list[float]]], F: list[list[float]] | list[list[list[float]]]) -> dict[str, Any]:
    """Compute Cauchy stress from first Piola-Kirchhoff stress and deformation gradient."""
    damask = import_damask()
    P_tensor = np.asarray(P, dtype=float)
    F_tensor = np.asarray(F, dtype=float)
    result = damask.mechanics.stress_Cauchy(P_tensor, F_tensor)
    return {
        "ok": True,
        "P_shape": list(P_tensor.shape),
        "F_shape": list(F_tensor.shape),
        "summary": summarize_array(result),
    }


__all__ = ["compute_cauchy_stress", "compute_strain"]
