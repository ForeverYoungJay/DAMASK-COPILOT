"""Result tools mapped from DAMASK post-processing docs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd

from damask_mcp_adapter.serializers import write_dataframe_csv
from damask_mcp_adapter.validators import ensure_existing_file, ensure_path_within_workspaces, ensure_workspace_write_path
from damask_mcp_adapter.workspace import import_damask


def _json_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _json_structure(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [_json_structure(item) for item in value.tolist()]
    if isinstance(value, (list, tuple)):
        return [_json_structure(item) for item in value]
    return _json_scalar(value)


def _collect_arrays(node: Any, found: list[np.ndarray]) -> None:
    if isinstance(node, np.ma.MaskedArray):
        found.append(np.asarray(node.filled(np.nan)))
        return
    if isinstance(node, np.ndarray):
        found.append(node)
        return
    if isinstance(node, dict):
        for value in node.values():
            _collect_arrays(value, found)


def _first_3x3_average(arrays: list[np.ndarray]) -> np.ndarray | None:
    for array in arrays:
        arr = np.asarray(array)
        if arr.ndim >= 2 and arr.shape[-2:] == (3, 3):
            return np.mean(arr.reshape((-1, 3, 3)), axis=0)
    return None


def inspect_hdf5_result(path: str, max_items: int = 200) -> dict[str, Any]:
    """Inspect an HDF5 file structure without loading large datasets."""
    try:
        hdf5_path = ensure_existing_file(path)
        items: list[dict[str, Any]] = []

        def visitor(name: str, node: h5py.Group | h5py.Dataset) -> None:
            if len(items) >= max_items:
                return
            item: dict[str, Any] = {
                "name": name or "/",
                "type": type(node).__name__,
                "attrs": {str(key): _json_structure(value) for key, value in node.attrs.items()},
            }
            if isinstance(node, h5py.Dataset):
                item["shape"] = list(node.shape)
                item["dtype"] = str(node.dtype)
            else:
                item["member_count"] = len(node.keys())
            items.append(item)

        with h5py.File(hdf5_path, "r") as handle:
            handle.visititems(visitor)
            root_attrs = {str(key): _json_structure(value) for key, value in handle.attrs.items()}

        return {
            "ok": True,
            "path": str(hdf5_path),
            "max_items": max_items,
            "item_count": len(items),
            "truncated": len(items) >= max_items,
            "root_attrs": root_attrs,
            "items": items,
        }
    except Exception as exc:
        return {"ok": False, "path": str(Path(path).expanduser().resolve()), "error": f"{type(exc).__name__}: {exc}"}


def inspect_result_file(path: str) -> dict[str, Any]:
    """Inspect a DAMASK result file through damask.Result."""
    try:
        input_path = ensure_existing_file(path)
        damask = import_damask()
        result = damask.Result(input_path)
        return {
            "ok": True,
            "path": str(input_path),
            "damask_class": "Result",
            "version_major": int(result.version_major),
            "version_minor": int(result.version_minor),
            "structured": bool(result.structured),
            "increments": list(result.increments),
            "times": [float(value) for value in result.times],
            "phases": list(result.phases),
            "homogenizations": list(result.homogenizations),
            "fields": list(result.fields),
            "simulation_setup_files": list(result.simulation_setup_files),
            "list_data_preview": result.list_data()[:50],
        }
    except Exception as exc:
        return {"ok": False, "path": str(Path(path).expanduser().resolve()), "error": f"{type(exc).__name__}: {exc}"}


def _mutate_result(path: str, method_name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    result_path = ensure_path_within_workspaces(path)
    damask = import_damask()
    result = damask.Result(result_path)
    try:
        getattr(result, method_name)(*args, **kwargs)
        refreshed = damask.Result(result_path)
        return {
            "ok": True,
            "path": str(result_path),
            "method": method_name,
            "fields": list(refreshed.fields),
            "list_data_preview": refreshed.list_data()[:30],
        }
    except Exception as exc:
        return {"ok": False, "path": str(result_path), "method": method_name, "error": f"{type(exc).__name__}: {exc}"}


def list_result_data(path: str) -> dict[str, Any]:
    """List active datasets in a DAMASK result file."""
    summary = inspect_result_file(path)
    if not summary["ok"]:
        return summary
    damask = import_damask()
    result = damask.Result(Path(path).expanduser().resolve())
    lines = result.list_data()
    return {"ok": True, "path": summary["path"], "count": len(lines), "data": lines[:200], "truncated": len(lines) > 200}


def list_result_increments(path: str) -> dict[str, Any]:
    """List visible increments in a DAMASK result file."""
    summary = inspect_result_file(path)
    if not summary["ok"]:
        return summary
    return {"ok": True, "path": summary["path"], "increments": summary["increments"], "times": summary["times"]}


def list_result_fields(path: str) -> dict[str, Any]:
    """List visible fields in a DAMASK result file."""
    summary = inspect_result_file(path)
    if not summary["ok"]:
        return summary
    return {"ok": True, "path": summary["path"], "fields": summary["fields"]}


def add_strain(path: str, F: str = "F", t: str = "V", m: float = 0.0) -> dict[str, Any]:
    """Add strain data to a DAMASK result file in-place."""
    return _mutate_result(path, "add_strain", F, t, m)


def add_equivalent_mises(path: str, T_sym: str, kind: str | None = None) -> dict[str, Any]:
    """Add von Mises equivalent data to a DAMASK result file in-place."""
    return _mutate_result(path, "add_equivalent_Mises", T_sym, kind)


def add_deviator(path: str, T: str) -> dict[str, Any]:
    """Add tensor deviator data to a DAMASK result file in-place."""
    return _mutate_result(path, "add_deviator", T)


def add_spherical(path: str, T: str) -> dict[str, Any]:
    """Add tensor spherical data to a DAMASK result file in-place."""
    return _mutate_result(path, "add_spherical", T)


def add_gradient(path: str, f: str) -> dict[str, Any]:
    """Add gradient data to a DAMASK result file in-place."""
    return _mutate_result(path, "add_gradient", f)


def add_divergence(path: str, f: str) -> dict[str, Any]:
    """Add divergence data to a DAMASK result file in-place."""
    return _mutate_result(path, "add_divergence", f)


def add_curl(path: str, f: str) -> dict[str, Any]:
    """Add curl data to a DAMASK result file in-place."""
    return _mutate_result(path, "add_curl", f)


def extract_volume_average(path: str, field: str, output_csv: str | None = None) -> dict[str, Any]:
    """Extract per-increment volume averages for a result field."""
    try:
        input_path = ensure_existing_file(path)
        damask = import_damask()
        result = damask.Result(input_path)
        rows: list[dict[str, Any]] = []
        for increment, time_value in zip(result.increments, result.times):
            placed = result.view(increments=[increment]).place(output=field, flatten=False, prune=True)
            arrays: list[np.ndarray] = []
            _collect_arrays(placed, arrays)
            if not arrays:
                continue
            means = [float(np.nanmean(np.asarray(array, dtype=float))) for array in arrays if np.asarray(array).size]
            rows.append({"increment": increment, "time": float(time_value), "field": field, "volume_average": float(np.mean(means)) if means else None})
        if not rows:
            return {"ok": False, "path": str(input_path), "field": field, "error": f"Field not found or could not be placed: {field}"}
        dataframe = pd.DataFrame(rows)
        output_path = write_dataframe_csv(dataframe, output_csv) if output_csv is not None else None
        return {"ok": True, "path": str(input_path), "field": field, "rows": len(rows), "preview": dataframe.head(10).to_dict(orient="records"), "output_csv": str(output_path) if output_path is not None else None}
    except Exception as exc:
        return {"ok": False, "path": str(Path(path).expanduser().resolve()), "field": field, "error": f"{type(exc).__name__}: {exc}"}


def extract_stress_strain_curve(path: str, output_csv: str) -> dict[str, Any]:
    """Extract a simple stress-strain curve from volume-averaged F and P."""
    try:
        input_path = ensure_existing_file(path)
        damask = import_damask()
        result = damask.Result(input_path)
        rows: list[dict[str, Any]] = []
        for increment, time_value in zip(result.increments, result.times):
            view = result.view(increments=[increment])
            F_arrays: list[np.ndarray] = []
            P_arrays: list[np.ndarray] = []
            _collect_arrays(view.place(output="F", flatten=False, prune=True), F_arrays)
            _collect_arrays(view.place(output="P", flatten=False, prune=True), P_arrays)
            F_avg = _first_3x3_average(F_arrays)
            P_avg = _first_3x3_average(P_arrays)
            if F_avg is None or P_avg is None:
                return {"ok": False, "path": str(input_path), "error": "Could not derive averaged F and P tensors from the result file."}
            try:
                strain_tensor = damask.mechanics.strain(F_avg[np.newaxis, ...], "V", 0.0)[0]
                stress_tensor = damask.mechanics.stress_Cauchy(P_avg[np.newaxis, ...], F_avg[np.newaxis, ...])[0]
                strain_xx = float(strain_tensor[0, 0])
                stress_xx = float(stress_tensor[0, 0])
            except Exception:
                strain_xx = float(F_avg[0, 0] - 1.0)
                stress_xx = float(P_avg[0, 0])
            rows.append({"increment": increment, "time": float(time_value), "strain_xx": strain_xx, "stress_xx": stress_xx})
        dataframe = pd.DataFrame(rows)
        output_path = write_dataframe_csv(dataframe, output_csv)
        return {"ok": True, "path": str(input_path), "rows": len(rows), "preview": dataframe.head(10).to_dict(orient="records"), "output_csv": str(output_path)}
    except Exception as exc:
        return {"ok": False, "path": str(Path(path).expanduser().resolve()), "error": f"{type(exc).__name__}: {exc}"}


def export_result_vtk(path: str, output_dir: str) -> dict[str, Any]:
    """Export a DAMASK result file to VTK files under workspaces/."""
    try:
        input_path = ensure_existing_file(path)
        target_dir = ensure_workspace_write_path(output_dir)
        damask = import_damask()
        result = damask.Result(input_path)
        result.export_VTK(target_dir=target_dir, parallel=False)
        exported = sorted(str(item) for item in target_dir.glob("*") if item.suffix in {".vti", ".vtu", ".vtp"})
        return {"ok": True, "path": str(input_path), "output_dir": str(target_dir), "exported_files": exported, "count": len(exported)}
    except Exception as exc:
        return {"ok": False, "path": str(Path(path).expanduser().resolve()), "output_dir": str(Path(output_dir).expanduser().resolve()), "error": f"{type(exc).__name__}: {exc}"}


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
