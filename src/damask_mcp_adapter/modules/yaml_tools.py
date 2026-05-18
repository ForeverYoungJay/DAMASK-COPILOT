"""Pre-processing YAML tools mapped from the official DAMASK docs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from damask_mcp_adapter.serializers import to_jsonable
from damask_mcp_adapter.validators import ensure_existing_file, ensure_workspace_write_path
from damask_mcp_adapter.workspace import import_damask


def write_yaml_file(path: str, data: dict[str, Any]) -> dict[str, Any]:
    """Write a generic YAML file under workspaces/ using damask.YAML."""
    output_path = ensure_workspace_write_path(path)
    damask = import_damask()
    document = damask.YAML(data)
    document.save(output_path)
    return {
        "ok": True,
        "path": str(output_path),
        "damask_class": "YAML",
        "data": to_jsonable(data),
    }


def read_yaml_file(path: str) -> dict[str, Any]:
    """Read a YAML file and return its parsed mapping."""
    try:
        input_path = ensure_existing_file(path)
        with input_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        return {
            "ok": True,
            "path": str(input_path),
            "data": to_jsonable(data),
        }
    except Exception as exc:
        return {
            "ok": False,
            "path": str(Path(path).expanduser().resolve()),
            "error": f"{type(exc).__name__}: {exc}",
        }


def validate_yaml_file(path: str) -> dict[str, Any]:
    """Validate that a YAML file can be parsed into a mapping."""
    result = read_yaml_file(path)
    if not result["ok"]:
        return result
    data = result["data"]
    is_mapping = isinstance(data, dict)
    return {
        "ok": is_mapping,
        "path": result["path"],
        "is_mapping": is_mapping,
        "keys": sorted(data.keys()) if is_mapping else [],
    }


__all__ = ["read_yaml_file", "validate_yaml_file", "write_yaml_file"]
