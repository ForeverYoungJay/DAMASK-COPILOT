"""Safe runner helpers for DAMASK_grid."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from damask_mcp_adapter.validators import ensure_existing_directory, ensure_existing_file, ensure_path_within_workspaces, resolve_workspace_dir
from damask_mcp_adapter.workspace import project_root

RESULT_SUFFIXES = {".hdf5", ".h5", ".vti", ".vtu", ".vtp", ".xdmf", ".csv"}


def _candidate_executables() -> list[Path]:
    candidates: list[Path] = []
    located = shutil.which("DAMASK_grid")
    if located:
        candidates.append(Path(located))
    local_candidates = [
        project_root() / "damask-3.0.2" / "bin" / "DAMASK_grid",
        project_root() / "damask-3.0.2" / "build" / "DAMASK_grid",
        project_root() / "damask-3.0.2" / "src" / "grid" / "DAMASK_grid",
    ]
    for candidate in local_candidates:
        if candidate.exists():
            candidates.append(candidate)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        resolved = str(path.resolve())
        if resolved not in seen:
            unique.append(path.resolve())
            seen.add(resolved)
    return unique


def find_damask_executables() -> dict[str, Any]:
    """Find DAMASK_grid executables on PATH and in common local build locations."""
    candidates = _candidate_executables()
    return {
        "ok": True,
        "count": len(candidates),
        "executables": [str(path) for path in candidates],
    }


def list_workspace_files(workspace: str) -> dict[str, Any]:
    """List files under a named workspace."""
    try:
        workspace_dir = ensure_existing_directory(resolve_workspace_dir(workspace))
        files = sorted(str(path) for path in workspace_dir.rglob("*") if path.is_file())
        return {"ok": True, "workspace": workspace, "count": len(files), "files": files}
    except Exception as exc:
        return {"ok": False, "workspace": workspace, "error": f"{type(exc).__name__}: {exc}"}


def collect_result_files(workspace: str) -> dict[str, Any]:
    """Collect result-like files under a named workspace."""
    listing = list_workspace_files(workspace)
    if not listing["ok"]:
        return listing
    files = [path for path in listing["files"] if Path(path).suffix.lower() in RESULT_SUFFIXES]
    return {"ok": True, "workspace": workspace, "count": len(files), "files": files}


def run_damask_grid(
    workspace: str,
    geometry: str,
    load: str,
    material: str,
    timeout_seconds: int = 3600,
) -> dict[str, Any]:
    """Run DAMASK_grid with workspace-local input files using a safe subprocess call."""
    try:
        executables = _candidate_executables()
        if not executables:
            return {
                "ok": False,
                "workspace": workspace,
                "error": "DAMASK_grid executable not found. Build or install DAMASK_grid first.",
            }
        workspace_dir = ensure_existing_directory(resolve_workspace_dir(workspace))
        geometry_path = ensure_path_within_workspaces(workspace_dir / geometry)
        load_path = ensure_path_within_workspaces(workspace_dir / load)
        material_path = ensure_path_within_workspaces(workspace_dir / material)
        ensure_existing_file(geometry_path)
        ensure_existing_file(load_path)
        ensure_existing_file(material_path)
        executable = executables[0]
        command = [
            str(executable),
            "--geom",
            str(geometry_path),
            "--load",
            str(load_path),
            "--material",
            str(material_path),
            "--workingdir",
            str(workspace_dir),
        ]
        process = subprocess.run(
            command,
            cwd=workspace_dir,
            env=os.environ.copy(),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "ok": process.returncode == 0,
            "workspace": workspace,
            "executable": str(executable),
            "returncode": int(process.returncode),
            "stdout_tail": process.stdout.splitlines()[-50:],
            "stderr_tail": process.stderr.splitlines()[-50:],
            "result_files": collect_result_files(workspace).get("files", []),
        }
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "workspace": workspace, "error": f"TimeoutExpired: {exc}"}
    except Exception as exc:
        return {"ok": False, "workspace": workspace, "error": f"{type(exc).__name__}: {exc}"}


__all__ = [
    "collect_result_files",
    "find_damask_executables",
    "list_workspace_files",
    "run_damask_grid",
]
