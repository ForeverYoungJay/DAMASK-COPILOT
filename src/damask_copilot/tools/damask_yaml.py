"""Deterministic builders for DAMASK YAML-like inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from damask_copilot.mcp_clients.damask_preprocess_client import DAMASKPreprocessClient


def build_material_yaml(spec: dict[str, Any], output_path: str) -> str:
    """Build a material.yaml, preferring the preprocess MCP client when safe."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    phase_name = spec.get("phase_name", spec.get("material_system", "phase_0"))
    homogenization_name = spec.get("homogenization_name", "SX")
    orientation = spec.get("orientation", [1.0, 0.0, 0.0, 0.0])
    volume_fraction = float(spec.get("volume_fraction", 1.0))

    material_entries = spec.get("material_entries")
    if not material_entries:
        material_entries = [
            {
                "homogenization": homogenization_name,
                "constituents": [
                    {
                        "phase": phase_name,
                        "O": orientation,
                        "v": volume_fraction,
                    }
                ],
            }
        ]

    payload = {
        "homogenization": spec.get(
            "homogenization",
            {homogenization_name: {"N_constituents": 1, "mechanical": {"type": "pass"}}},
        ),
        "phase": spec.get(
            "phase",
            {
                phase_name: {
                    "lattice": spec.get("lattice", "cF"),
                    "mechanical": {
                        "elastic": spec.get("elastic", {"type": "Hooke", "C_11": 168400000000.0, "C_12": 121400000000.0, "C_44": 75400000000.0}),
                        "plastic": spec.get(
                            "plastic",
                            {"type": "phenopowerlaw", "N_sl": [12], "a_sl": 2.25, "dot_gamma_0_sl": 0.001, "h_0_sl-sl": 355000000.0, "n_sl": 20, "xi_0_sl": [31000000.0], "xi_inf_sl": [63000000.0]},
                        ),
                    },
                }
            },
        ),
        "material": material_entries,
    }

    if _try_build_material_with_mcp(spec=spec, path=path, payload=payload):
        return str(path)

    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return str(path)


def build_load_yaml(spec: dict[str, Any], output_path: str) -> str:
    """Build a load.yaml, preferring preprocess MCP helpers when safe."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "solver": spec.get("solver", {"mechanical": "spectral_basic"}),
        "loadstep": [
            {
                "boundary_conditions": spec.get(
                    "boundary_conditions",
                    {
                        "mechanical": {
                            "F": spec.get(
                                "deformation_gradient",
                                [[1.01, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                            )
                        }
                    },
                ),
                "discretization": {"t": float(spec.get("time", 1.0)), "N": int(spec.get("steps", 10))},
                "f_out": int(spec.get("f_out", 1)),
            }
        ],
    }
    if _try_build_load_with_mcp(spec=spec, path=path) and _is_valid_yaml_mapping(path, "loadstep"):
        return str(path)

    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return str(path)


def build_numerics_yaml(spec: dict[str, Any], output_path: str) -> str:
    """Build a numerics.yaml file, preferring the preprocess MCP YAML writer."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = spec.get(
        "numerics",
        {
            "solver": {
                "grid": {
                    "N_staggered_iter_max": 10,
                    "eps_abs_div_P": 1.0e-10,
                    "eps_rel_div_P": 1.0e-4,
                    "eps_abs_P": 1.0e3,
                    "eps_rel_P": 5.0e-4,
                }
            }
        },
    )
    try:
        client = DAMASKPreprocessClient()
        client.write_yaml_file(path=str(path), data=payload)
        if _is_valid_yaml_mapping(path):
            return str(path)
    except Exception:
        pass
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return str(path)


def _try_build_material_with_mcp(*, spec: dict[str, Any], path: Path, payload: dict[str, Any]) -> bool:
    try:
        client = DAMASKPreprocessClient()
        material_entries = spec.get("material_entries")
        if material_entries:
            client.create_material_yaml_from_template(
                path=str(path),
                homogenization=payload["homogenization"],
                phase=payload["phase"],
                material=payload["material"],
            )
        else:
            client.create_material_yaml(
                path=str(path),
                material_name=spec.get("material_system", spec.get("phase_name", "material")),
                phase_name=spec.get("phase_name", spec.get("material_system", "phase_0")),
                lattice=spec.get("lattice", "cF"),
                elastic=spec.get("elastic", {}),
                plastic=spec.get("plastic"),
            )
        return _is_valid_yaml_mapping(path, "material")
    except Exception:
        return False


def _try_build_load_with_mcp(*, spec: dict[str, Any], path: Path) -> bool:
    try:
        client = DAMASKPreprocessClient()
        mode = str(spec.get("loading_mode", spec.get("workflow_type", "uniaxial_tension"))).lower()
        final_strain = float(spec.get("final_strain", 0.02))
        strain_rate = float(spec.get("strain_rate", 1.0e-3))
        steps = int(spec.get("steps", 10))
        if "compression" in mode:
            client.create_simple_compression_load_yaml(
                path=str(path),
                strain_rate=strain_rate,
                final_strain=final_strain,
                steps=steps,
            )
            return True
        if any(token in mode for token in ("tension", "simulation_run", "calibration", "comparison", "discovery")):
            client.create_simple_tension_load_yaml(
                path=str(path),
                strain_rate=strain_rate,
                final_strain=final_strain,
                steps=steps,
            )
            return True
        return False
    except Exception:
        return False


def _is_valid_yaml_mapping(path: Path, required_key: str | None = None) -> bool:
    if not path.exists():
        return False
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    if not isinstance(payload, dict):
        return False
    if required_key is not None and required_key not in payload:
        return False
    return True
