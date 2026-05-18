"""Grid tools mapped from DAMASK pre-processing docs."""

from __future__ import annotations

from damask_mcp_adapter.serializers import summarize_array
from damask_mcp_adapter.validators import ensure_existing_file, ensure_workspace_write_path
from damask_mcp_adapter.workspace import import_damask


def create_voronoi_grid(path: str, cells: list[int], size: list[float], grains: int, seed: int = 0) -> dict:
    """Create a Voronoi tessellation grid and save it as .vti under workspaces/."""
    output_path = ensure_workspace_write_path(path)
    damask = import_damask()
    seeds = damask.seeds.from_random(size, grains, cells=cells, rng_seed=seed)
    grid = damask.GeomGrid.from_Voronoi_tessellation(cells, size, seeds)
    grid.save(output_path)
    return {
        "ok": True,
        "path": str(output_path),
        "damask_class": "GeomGrid",
        "cells": [int(value) for value in grid.cells],
        "size": [float(value) for value in grid.size],
        "origin": [float(value) for value in grid.origin],
        "grain_count": grains,
        "seed_summary": summarize_array(seeds),
        "material_count": int(grid.N_materials),
    }


def inspect_grid(path: str) -> dict:
    """Inspect a DAMASK VTI grid file."""
    try:
        input_path = ensure_existing_file(path)
        damask = import_damask()
        grid = damask.GeomGrid.load(input_path)
        return {
            "ok": True,
            "path": str(input_path),
            "cells": [int(value) for value in grid.cells],
            "size": [float(value) for value in grid.size],
            "origin": [float(value) for value in grid.origin],
            "material_count": int(grid.N_materials),
            "material_summary": summarize_array(grid.material),
            "initial_conditions": sorted(grid.initial_conditions.keys()),
            "comments": list(grid.comments),
        }
    except Exception as exc:
        from pathlib import Path

        return {
            "ok": False,
            "path": str(Path(path).expanduser().resolve()),
            "error": f"{type(exc).__name__}: {exc}",
        }


def scale_grid(path: str, cells: list[int]) -> dict:
    """Scale a DAMASK grid to new cell counts and overwrite the workspace file."""
    grid_path = ensure_workspace_write_path(path, create_parent=False)
    damask = import_damask()
    grid = damask.GeomGrid.load(grid_path)
    scaled = grid.scale(cells)
    scaled.save(grid_path)
    return {
        "ok": True,
        "path": str(grid_path),
        "cells": [int(value) for value in scaled.cells],
        "size": [float(value) for value in scaled.size],
        "material_count": int(scaled.N_materials),
    }


def renumber_grid(path: str) -> dict:
    """Renumber material IDs in a DAMASK grid and overwrite the workspace file."""
    grid_path = ensure_workspace_write_path(path, create_parent=False)
    damask = import_damask()
    grid = damask.GeomGrid.load(grid_path)
    updated = grid.renumber()
    updated.save(grid_path)
    return {
        "ok": True,
        "path": str(grid_path),
        "material_summary": summarize_array(updated.material),
    }


def clean_grid(
    path: str,
    distance: float = 1.7320508075688772,
    selection: list[int] | None = None,
    invert_selection: bool = False,
    periodic: bool = True,
    seed: int = 0,
) -> dict:
    """Smooth a DAMASK grid with GeomGrid.clean and overwrite the workspace file."""
    grid_path = ensure_workspace_write_path(path, create_parent=False)
    damask = import_damask()
    grid = damask.GeomGrid.load(grid_path)
    cleaned = grid.clean(
        distance=distance,
        selection=selection,
        invert_selection=invert_selection,
        periodic=periodic,
        rng_seed=seed,
    )
    cleaned.save(grid_path)
    return {
        "ok": True,
        "path": str(grid_path),
        "distance": distance,
        "material_summary": summarize_array(cleaned.material),
    }


__all__ = [
    "clean_grid",
    "create_voronoi_grid",
    "inspect_grid",
    "renumber_grid",
    "scale_grid",
]
