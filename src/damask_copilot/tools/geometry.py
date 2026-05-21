"""Geometry builders and inspectors for deterministic validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from damask_copilot.mcp_clients.damask_preprocess_client import DAMASKPreprocessClient


def build_grid_geometry(spec: dict[str, Any], output_path: str) -> str:
    """Build geometry, with an optional MCP-backed path and a deterministic fallback."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    material_indices = list(spec.get("material_indices", []))
    if not material_indices:
        grains = int(spec.get("grains", 1))
        material_indices = list(range(max(grains, 1)))

    payload = {
        "format": "damask_copilot_stub_geometry_v1",
        "cells": list(spec.get("cells", [8, 8, 8])),
        "size": list(spec.get("size", [1.0, 1.0, 1.0])),
        "grains": int(spec.get("grains", max(len(material_indices), 1))),
        "material_indices": material_indices,
    }

    if spec.get("use_mcp_geometry", False):
        try:
            client = DAMASKPreprocessClient()
            result = client.create_voronoi_grid(
                path=str(path),
                cells=payload["cells"],
                size=payload["size"],
                grains=payload["grains"],
                seed=int(spec.get("seed", 0)),
            )
            if result.get("ok", False) and path.exists():
                return str(path)
        except Exception:
            pass

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


def inspect_geometry_material_indices(geometry_path: str) -> dict[str, Any]:
    """Inspect geometry material indices from a stub geometry file or YAML/JSON metadata."""
    path = Path(geometry_path)
    if not path.exists():
        return {"ok": False, "errors": [f"Geometry file does not exist: {geometry_path}"]}

    text = path.read_text(encoding="utf-8", errors="ignore")
    payload: Any | None = None
    for loader in (json.loads, yaml.safe_load):
        try:
            payload = loader(text)
            break
        except Exception:
            continue

    if isinstance(payload, dict) and "material_indices" in payload:
        indices = [int(value) for value in payload.get("material_indices", [])]
        unique_indices = sorted(set(indices))
        return {
            "ok": True,
            "unique_indices": unique_indices,
            "max_index": max(unique_indices) if unique_indices else 0,
            "material_count": len(unique_indices),
            "grains": int(payload.get("grains", len(unique_indices) or 1)),
        }

    try:
        inspected = DAMASKPreprocessClient().inspect_grid(path=str(path))
        if inspected.get("ok", False):
            material_count = int(inspected.get("material_count", 0))
            unique_indices = list(range(material_count)) if material_count > 0 else [0]
            return {
                "ok": True,
                "unique_indices": unique_indices,
                "max_index": max(unique_indices) if unique_indices else 0,
                "material_count": material_count,
                "grains": int(inspected.get("grains", material_count or 1)),
                "source": "mcp_inspect_grid",
            }
    except Exception:
        pass

    return {
        "ok": False,
        "errors": [
            "Geometry file is not in an inspectable stub format. "
            "Use build_grid_geometry() or provide geometry metadata with material_indices."
        ],
    }
