"""Load case helpers built on top of DAMASK LoadcaseGrid."""

from __future__ import annotations

from typing import Any

from damask_mcp_adapter.validators import ensure_workspace_write_path
from damask_mcp_adapter.workspace import import_damask


def _simple_uniaxial_load(direction: int, strain_rate: float, final_strain: float, steps: int) -> dict[str, Any]:
    deformation: list[list[float | str]] = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ]
    stress: list[list[float | str]] = [
        ["x", "x", "x"],
        ["x", "x", "x"],
        ["x", "x", "x"],
    ]
    deformation[direction][direction] = float(strain_rate)
    for diagonal in range(3):
        if diagonal != direction:
            deformation[diagonal][diagonal] = "x"
            stress[diagonal][diagonal] = 0.0
    return {
        "boundary_conditions": {"mechanical": {"dot_F": deformation, "P": stress}},
        "discretization": {"t": float(abs(final_strain / strain_rate)) if strain_rate else 0.0, "N": int(steps)},
        "f_out": 1,
    }


def _write_loadcase(path: str, loadcase: Any) -> dict[str, Any]:
    output_path = ensure_workspace_write_path(path)
    loadcase.save(output_path)
    return {
        "ok": True,
        "path": str(output_path),
        "damask_class": "LoadcaseGrid",
        "solver": dict(loadcase.get("solver", {})),
        "loadstep_count": len(loadcase.get("loadstep", [])),
        "data": dict(loadcase),
    }


def create_simple_tension_load_yaml(path: str, strain_rate: float, final_strain: float, steps: int) -> dict[str, Any]:
    """Create a simple uniaxial tension grid-solver load case."""
    damask = import_damask()
    loadcase = damask.LoadcaseGrid(
        solver={"mechanical": "spectral_basic"},
        loadstep=[_simple_uniaxial_load(0, abs(strain_rate), abs(final_strain), steps)],
    )
    return _write_loadcase(path, loadcase)


def create_simple_compression_load_yaml(path: str, strain_rate: float, final_strain: float, steps: int) -> dict[str, Any]:
    """Create a simple uniaxial compression grid-solver load case."""
    damask = import_damask()
    signed_strain = -abs(final_strain)
    loadcase = damask.LoadcaseGrid(
        solver={"mechanical": "spectral_basic"},
        loadstep=[_simple_uniaxial_load(0, abs(strain_rate), signed_strain, steps)],
    )
    return _write_loadcase(path, loadcase)


__all__ = [
    "create_simple_compression_load_yaml",
    "create_simple_tension_load_yaml",
]
