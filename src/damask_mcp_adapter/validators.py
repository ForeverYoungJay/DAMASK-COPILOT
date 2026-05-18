"""Validation helpers for safe MCP wrappers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from damask_mcp_adapter.workspace import workspaces_root

WORKSPACE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def validate_workspace_name(name: str) -> str:
    """Validate a workspace name."""
    if not WORKSPACE_NAME_RE.fullmatch(name):
        raise ValueError("Workspace name may contain only letters, digits, dot, underscore, and dash.")
    return name


def is_within_directory(path: Path, root: Path) -> bool:
    """Return whether a path is inside a root directory."""
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def resolve_workspace_dir(name: str) -> Path:
    """Resolve a workspace directory under workspaces/."""
    validate_workspace_name(name)
    return workspaces_root() / name


def ensure_workspace_write_path(path: str | Path, *, create_parent: bool = True) -> Path:
    """Resolve a writable path restricted to workspaces/."""
    workspace_root = workspaces_root().resolve()
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        parts = candidate.parts
        if parts and parts[0] == workspace_root.name:
            candidate = Path(*parts[1:]) if len(parts) > 1 else Path()
        resolved = (workspace_root / candidate).resolve()
    else:
        resolved = candidate.resolve()
    if not is_within_directory(resolved, workspace_root):
        raise ValueError(f"Write path must stay within {workspace_root}.")
    if create_parent:
        resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def ensure_path_within_workspaces(path: str | Path) -> Path:
    """Ensure that an existing or future path stays inside workspaces/."""
    workspace_root = workspaces_root().resolve()
    resolved = Path(path).expanduser().resolve()
    if not is_within_directory(resolved, workspace_root):
        raise ValueError(f"Path must stay within {workspace_root}.")
    return resolved


def ensure_existing_path(path: str | Path) -> Path:
    """Ensure that a path exists."""
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {resolved}")
    return resolved


def ensure_existing_file(path: str | Path) -> Path:
    """Ensure that a file exists."""
    resolved = ensure_existing_path(path)
    if not resolved.is_file():
        raise FileNotFoundError(f"Path is not a file: {resolved}")
    return resolved


def ensure_existing_directory(path: str | Path) -> Path:
    """Ensure that a directory exists."""
    resolved = ensure_existing_path(path)
    if not resolved.is_dir():
        raise FileNotFoundError(f"Path is not a directory: {resolved}")
    return resolved


def validate_mapping(data: Any) -> dict[str, Any]:
    """Validate that YAML-like content is a dictionary."""
    if not isinstance(data, dict):
        raise TypeError("Expected a dictionary.")
    return data
