"""Material configuration tools mapped from DAMASK pre-processing docs."""

from __future__ import annotations

import contextlib
import io
from pathlib import Path
from typing import Any

from damask_mcp_adapter.serializers import to_jsonable
from damask_mcp_adapter.validators import ensure_existing_file, ensure_workspace_write_path
from damask_mcp_adapter.workspace import import_damask


def create_empty_material_yaml(path: str) -> dict[str, Any]:
    """Create an empty DAMASK material.yaml skeleton under workspaces/."""
    output_path = ensure_workspace_write_path(path)
    damask = import_damask()
    config = damask.ConfigMaterial()
    config.save(output_path)
    return {
        "ok": True,
        "path": str(output_path),
        "damask_class": "ConfigMaterial",
        "keys": sorted(dict(config).keys()),
    }


def inspect_material_yaml(path: str) -> dict[str, Any]:
    """Inspect a DAMASK material.yaml file."""
    try:
        input_path = ensure_existing_file(path)
        damask = import_damask()
        config = damask.ConfigMaterial.load(input_path)
        data = dict(config)
        return {
            "ok": True,
            "path": str(input_path),
            "phase_names": sorted(data.get("phase", {}).keys()),
            "homogenization_names": sorted(data.get("homogenization", {}).keys()),
            "material_count": len(data.get("material", [])),
            "keys": sorted(data.keys()),
            "data": to_jsonable(data),
        }
    except Exception as exc:
        return {
            "ok": False,
            "path": str(Path(path).expanduser().resolve()),
            "error": f"{type(exc).__name__}: {exc}",
        }


def validate_material_yaml(path: str) -> dict[str, Any]:
    """Validate a DAMASK material.yaml file with DAMASK's own checks."""
    try:
        input_path = ensure_existing_file(path)
        damask = import_damask()
        config = damask.ConfigMaterial.load(input_path)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            is_complete = bool(config.is_complete)
            is_valid = bool(config.is_valid)
        messages = [line for line in stream.getvalue().splitlines() if line.strip()]
        return {
            "ok": is_complete and is_valid,
            "path": str(input_path),
            "is_complete": is_complete,
            "is_valid": is_valid,
            "messages": messages,
        }
    except Exception as exc:
        return {
            "ok": False,
            "path": str(Path(path).expanduser().resolve()),
            "error": f"{type(exc).__name__}: {exc}",
        }


def add_material_entry(
    path: str,
    homogenization: str,
    phase: str,
    orientation_quaternion: list[float],
    volume_fraction: float = 1.0,
) -> dict[str, Any]:
    """Add one material entry to an existing DAMASK material.yaml under workspaces/."""
    output_path = ensure_workspace_write_path(path, create_parent=False)
    damask = import_damask()
    config = damask.ConfigMaterial.load(output_path)
    updated = config.material_add(
        homogenization=homogenization,
        phase=phase,
        O=orientation_quaternion,
        v=volume_fraction,
    )
    updated.save(output_path)
    return {
        "ok": True,
        "path": str(output_path),
        "material_count": len(updated.get("material", [])),
        "phase_names": sorted(updated.get("phase", {}).keys()),
        "homogenization_names": sorted(updated.get("homogenization", {}).keys()),
    }


__all__ = [
    "add_material_entry",
    "create_empty_material_yaml",
    "inspect_material_yaml",
    "validate_material_yaml",
]
