"""Table tools mapped from DAMASK miscellaneous docs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from damask_mcp_adapter.serializers import summarize_array
from damask_mcp_adapter.validators import ensure_existing_file, ensure_workspace_write_path
from damask_mcp_adapter.workspace import import_damask


def load_table(path: str) -> dict[str, Any]:
    """Load a DAMASK table and return a compact summary."""
    table_path = ensure_existing_file(path)
    damask = import_damask()
    table = damask.Table.load(table_path)
    return inspect_table(path)


def inspect_table(path: str) -> dict[str, Any]:
    """Inspect a DAMASK table file."""
    table_path = ensure_existing_file(path)
    damask = import_damask()
    table = damask.Table.load(table_path)
    return {
        "ok": True,
        "path": str(table_path),
        "rows": len(table),
        "labels": list(table.labels),
        "shapes": {key: list(value) for key, value in table.shapes.items()},
        "comments": list(table.comments),
    }


def get_table_column(path: str, label: str, output_npy: str | None = None) -> dict[str, Any]:
    """Get one DAMASK table column as a compact summary."""
    table_path = ensure_existing_file(path)
    damask = import_damask()
    table = damask.Table.load(table_path)
    data = table.get(label)
    output_path = None
    if output_npy is not None:
        output_path = ensure_workspace_write_path(output_npy)
        import numpy as np

        np.save(output_path, data)
    return {
        "ok": True,
        "path": str(table_path),
        "label": label,
        "summary": summarize_array(data),
        "output_npy": str(output_path) if output_path is not None else None,
    }


def rename_table_column(path: str, old: str, new: str, output_path: str | None = None) -> dict[str, Any]:
    """Rename a DAMASK table column and save under workspaces/."""
    table_path = ensure_existing_file(path)
    target = ensure_workspace_write_path(output_path or table_path)
    damask = import_damask()
    table = damask.Table.load(table_path).rename(old, new)
    table.save(target)
    return {
        "ok": True,
        "path": str(target),
        "labels": list(table.labels),
    }


def sort_table_by(path: str, labels: str | list[str], ascending: bool = True, output_path: str | None = None) -> dict[str, Any]:
    """Sort a DAMASK table by one or more columns and save under workspaces/."""
    table_path = ensure_existing_file(path)
    target = ensure_workspace_write_path(output_path or table_path)
    damask = import_damask()
    table = damask.Table.load(table_path).sort_by(labels, ascending=ascending)
    table.save(target)
    return {
        "ok": True,
        "path": str(target),
        "labels": list(table.labels),
        "rows": len(table),
    }


__all__ = [
    "get_table_column",
    "inspect_table",
    "load_table",
    "rename_table_column",
    "sort_table_by",
]
