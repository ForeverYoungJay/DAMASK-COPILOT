"""Workspace and DAMASK source discovery helpers."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any


def project_root() -> Path:
    """Return the DAMASK Copilot project root."""
    return Path(__file__).resolve().parents[2]


def workspaces_root() -> Path:
    """Return the workspace root and create it if needed."""
    root = project_root() / "workspaces"
    root.mkdir(parents=True, exist_ok=True)
    return root


def damask_python_root() -> Path:
    """Return the local DAMASK Python source root."""
    return project_root() / "damask-3.0.2" / "python"


def ensure_damask_python_on_path() -> Path:
    """Ensure the local DAMASK Python source is importable."""
    path = damask_python_root()
    path_str = str(path)
    if path.exists() and path_str not in sys.path:
        sys.path.insert(0, path_str)
    return path


def import_damask() -> Any:
    """Import the DAMASK Python package from the local source tree."""
    ensure_damask_python_on_path()
    return importlib.import_module("damask")
