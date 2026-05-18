"""Utility tools mapped from DAMASK miscellaneous docs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from damask_mcp_adapter.serializers import summarize_array
from damask_mcp_adapter.validators import ensure_existing_file
from damask_mcp_adapter.workspace import import_damask


def inspect_dream3d_base_group(path: str) -> dict[str, Any]:
    """Inspect the detected DREAM3D base group."""
    file_path = ensure_existing_file(path)
    damask = import_damask()
    try:
        base_group = damask.util.DREAM3D_base_group(file_path)
        return {"ok": True, "path": str(file_path), "base_group": base_group}
    except Exception as exc:
        return {"ok": False, "path": str(file_path), "error": f"{type(exc).__name__}: {exc}"}


def inspect_dream3d_cell_data_group(path: str) -> dict[str, Any]:
    """Inspect the detected DREAM3D cell-data group."""
    file_path = ensure_existing_file(path)
    damask = import_damask()
    try:
        cell_data_group = damask.util.DREAM3D_cell_data_group(file_path)
        return {"ok": True, "path": str(file_path), "cell_data_group": cell_data_group}
    except Exception as exc:
        return {"ok": False, "path": str(file_path), "error": f"{type(exc).__name__}: {exc}"}


def miller_to_bravais(uvw: list[int] | None = None, hkl: list[int] | None = None) -> dict[str, Any]:
    """Convert 3-index Miller direction or plane indices to 4-index Miller-Bravais indices."""
    damask = import_damask()
    if uvw is not None:
        converted = damask.util.Miller_to_Bravais(uvw=uvw)
        return {"ok": True, "input": {"uvw": uvw}, "result": converted.tolist()}
    if hkl is not None:
        converted = damask.util.Miller_to_Bravais(hkl=hkl)
        return {"ok": True, "input": {"hkl": hkl}, "result": converted.tolist()}
    return {"ok": False, "error": "Provide either uvw or hkl."}


def bravais_to_miller(uvtw: list[int] | None = None, hkil: list[int] | None = None) -> dict[str, Any]:
    """Convert 4-index Miller-Bravais direction or plane indices to 3-index Miller indices."""
    damask = import_damask()
    if uvtw is not None:
        converted = damask.util.Bravais_to_Miller(uvtw=uvtw)
        return {"ok": True, "input": {"uvtw": uvtw}, "result": converted.tolist()}
    if hkil is not None:
        converted = damask.util.Bravais_to_Miller(hkil=hkil)
        return {"ok": True, "input": {"hkil": hkil}, "result": converted.tolist()}
    return {"ok": False, "error": "Provide either uvtw or hkil."}


__all__ = [
    "bravais_to_miller",
    "inspect_dream3d_base_group",
    "inspect_dream3d_cell_data_group",
    "miller_to_bravais",
]
