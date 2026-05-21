"""Deterministic post-processing helpers for DAMASK Copilot."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from damask_copilot.mcp_clients.damask_postprocess_client import DAMASKPostprocessClient


def extract_stress_strain(result_path: str) -> dict[str, Any]:
    """Extract a stress-strain curve from CSV-like data or DAMASK result output."""
    path = Path(result_path)
    if not path.exists():
        return {"ok": False, "status": "not_available", "error": f"Result file does not exist: {result_path}"}

    if path.suffix.lower() == ".csv":
        curve = _read_curve_csv(path)
        return {"ok": True, "status": "success", "curve": curve, "source": str(path)}

    try:
        temp_csv = path.with_suffix(".stress_strain.csv")
        output = DAMASKPostprocessClient().extract_stress_strain(path=str(path), output_csv=str(temp_csv))
        if not output.get("ok", False) or not temp_csv.exists():
            return {
                "ok": False,
                "status": "not_available",
                "error": output.get("error", "Stress-strain extraction failed."),
            }
        curve = _read_curve_csv(temp_csv)
        return {"ok": True, "status": "success", "curve": curve, "source": str(temp_csv)}
    except Exception as exc:
        return {
            "ok": False,
            "status": "not_available",
            "error": f"Post-processing is not available in this environment: {type(exc).__name__}: {exc}",
        }


def compute_yield_stress(curve: dict[str, list[float]]) -> dict[str, Any]:
    """Estimate a simple 0.2% offset-style yield stress proxy."""
    strain = np.asarray(curve.get("strain", []), dtype=float)
    stress = np.asarray(curve.get("stress", []), dtype=float)
    if len(strain) == 0 or len(stress) == 0:
        return {"ok": False, "error": "Curve is empty."}
    indices = np.where(strain >= 0.002)[0]
    yield_index = int(indices[0]) if len(indices) else len(stress) - 1
    return {"ok": True, "yield_stress": float(stress[yield_index]), "strain_at_yield": float(strain[yield_index])}


def compute_hardening_rate(curve: dict[str, list[float]]) -> dict[str, Any]:
    """Compute a simple average hardening rate from a stress-strain curve."""
    strain = np.asarray(curve.get("strain", []), dtype=float)
    stress = np.asarray(curve.get("stress", []), dtype=float)
    if len(strain) < 2 or len(stress) < 2:
        return {"ok": False, "error": "Curve requires at least two points."}
    gradient = np.gradient(stress, strain, edge_order=1)
    return {"ok": True, "hardening_rate": float(np.nanmean(gradient))}


def compare_experiment_simulation(sim_curve: dict[str, list[float]], exp_curve: dict[str, list[float]]) -> dict[str, Any]:
    """Compare simulation and experiment stress-strain curves on a shared strain grid."""
    sim_strain = np.asarray(sim_curve.get("strain", []), dtype=float)
    sim_stress = np.asarray(sim_curve.get("stress", []), dtype=float)
    exp_strain = np.asarray(exp_curve.get("strain", []), dtype=float)
    exp_stress = np.asarray(exp_curve.get("stress", []), dtype=float)
    if min(len(sim_strain), len(sim_stress), len(exp_strain), len(exp_stress)) == 0:
        return {"ok": False, "error": "Both curves must contain strain and stress data."}

    grid = np.linspace(max(sim_strain.min(), exp_strain.min()), min(sim_strain.max(), exp_strain.max()), num=25)
    sim_interp = np.interp(grid, sim_strain, sim_stress)
    exp_interp = np.interp(grid, exp_strain, exp_stress)
    delta = sim_interp - exp_interp
    return {
        "ok": True,
        "rmse": float(np.sqrt(np.mean(delta ** 2))),
        "max_abs_error": float(np.max(np.abs(delta))),
        "aligned_points": int(len(grid)),
    }


def plot_stress_strain(sim_curve: dict[str, list[float]], exp_curve: dict[str, list[float]], output_path: str) -> str:
    """Plot simulation and experiment stress-strain curves."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 4))
    if sim_curve.get("strain") and sim_curve.get("stress"):
        plt.plot(sim_curve["strain"], sim_curve["stress"], label="simulation")
    if exp_curve.get("strain") and exp_curve.get("stress"):
        plt.plot(exp_curve["strain"], exp_curve["stress"], label="experiment")
    plt.xlabel("strain")
    plt.ylabel("stress")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return str(path)


def postprocess_results(state: Any) -> dict[str, Any]:
    """Run deterministic post-processing and comparison against experiment when possible."""
    run_result = _state_value(state, "run_result") or {}
    experimental = _state_value(state, "experimental_data") or {}
    result_files = list(run_result.get("result_files", []))
    if not result_files:
        return {"ok": False, "status": "not_available", "error": "No result files were available for post-processing."}

    extracted = extract_stress_strain(result_files[0])
    if not extracted.get("ok", False):
        return extracted

    curve = extracted["curve"]
    output: dict[str, Any] = {
        "ok": True,
        "status": "success",
        "curve": curve,
        "yield_stress": compute_yield_stress(curve),
        "hardening_rate": compute_hardening_rate(curve),
    }

    exp_curve = experimental.get("curve")
    if exp_curve:
        output["comparison"] = compare_experiment_simulation(curve, exp_curve)
    return output


def _read_curve_csv(path: Path) -> dict[str, list[float]]:
    strain: list[float] = []
    stress: list[float] = []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_lower = {key.lower(): value for key, value in row.items()}
            strain_key = next((key for key in row_lower if "strain" in key), None)
            stress_key = next((key for key in row_lower if "stress" in key or key == "p"), None)
            if strain_key is None or stress_key is None:
                continue
            strain.append(float(row_lower[strain_key]))
            stress.append(float(row_lower[stress_key]))
    return {"strain": strain, "stress": stress}


def _state_value(state: Any, key: str) -> Any:
    if hasattr(state, key):
        return getattr(state, key)
    if hasattr(state, "get"):
        return state.get(key)
    return None
